__doc__ = """
Main module for running BRISE configuration balancing."""

import json
import logging
import os
import pickle
import threading
from collections import OrderedDict
from enum import Enum
from sys import argv
from warnings import filterwarnings

import pika
from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from core_entities.search_space import Hyperparameter, get_search_space_record
from default_config_handler.default_config_handler_selector import (
    get_default_config_handler
)
from logger.default_logger import BRISELogConfigurator
from model.predictor import Predictor
from repeater.repeater_selector import RepeaterOrchestration
from stop_condition.stop_condition_selector import (
    launch_stop_condition_threads
)
from tools.front_API import API
from tools.initial_config import (
    load_experiment_setup,
    validate_experiment_description
)
from tools.mongo_dao import MongoDB
from WorkerServiceClient.WSClient_events import WSClient

logging.getLogger("pika").setLevel(logging.WARNING)


class MainThread(threading.Thread):
    """
    This class runs Main functionality in a separate thread,
    connected to the `default_configuration_results_queue` and `configurations results queue` as a consumer.
    """

    class State(int, Enum):
        RUNNING = 0
        SHUTTING_DOWN = 1
        IDLE = 2

    def __init__(self, experiment_setup: [Experiment, Hyperparameter] = None):
        """
        The function for initializing main thread
        :param experiment_setup: fully initialized experiment, r.g from a POST request
        """
        super(MainThread, self).__init__()
        self._is_interrupted = False
        self.conf_lock = threading.Lock()
        self._state = self.State.IDLE
        self.experiment_setup = experiment_setup

        self.sub = API()  # front-end subscribers
        if __name__ == "__main__":
            self.logger = BRISELogConfigurator().get_logger(__name__)
        else:
            self.logger = logging.getLogger(__name__)

        self.experiment: Experiment = None
        self.connection: pika.BlockingConnection = None
        self.consume_channel = None
        self.predictor: Predictor = None
        self.wsc_client: WSClient = None
        self.repeater: RepeaterOrchestration = None
        self.database: MongoDB = None

    def run(self):
        """
        The entry point to the main node functionality - measuring default Configuration.
        When the default Configuration finishes its evaluation, the first set of Configurations will be
        sampled for evaluation (respectively, the queues for Configuration measurement results initialize).
        """
        self._state = self.State.RUNNING
        self.logger.info("Starting BRISE")
        self.sub.send('log', 'info', message="Starting BRISE")

        if not self.experiment_setup:
            # Check if main.py running with a specified experiment description file path
            if len(argv) > 1:
                exp_desc_file_path = argv[1]
            else:
                exp_desc_file_path = './Resources/EnergyExperiment/EnergyExperiment.json'
                log_msg = f"The Experiment Setup was not provided and the path to an experiment file was not specified." \
                          f" The default one will be executed: {exp_desc_file_path}"
                self.logger.warning(log_msg)
                self.sub.send('log', 'warning', message=log_msg)
            experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        else:
            experiment_description = self.experiment_setup["experiment_description"]
            search_space = self.experiment_setup["search_space"]

        validate_experiment_description(experiment_description)
        os.makedirs(experiment_description["General"]["results_storage"], exist_ok=True)

        # Initializing instance of Experiment - main data holder.
        self.experiment = Experiment(experiment_description, search_space)
        search_space.experiment_id = self.experiment.unique_id
        Configuration.set_task_config(self.experiment.description["TaskConfiguration"])

        # initialize connection to rabbitmq service
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                os.getenv("BRISE_EVENT_SERVICE_HOST"),
                int(os.getenv("BRISE_EVENT_SERVICE_AMQP_PORT"))
            )
        )
        self.consume_channel = self.connection.channel()

        # initialize connection to the database
        self.database = MongoDB(
            os.getenv("BRISE_DATABASE_HOST"),
            int(os.getenv("BRISE_DATABASE_PORT")),
            os.getenv("BRISE_DATABASE_NAME"),
            os.getenv("BRISE_DATABASE_USER"),
            os.getenv("BRISE_DATABASE_PASS")
        )

        # write initial settings to the database
        self.database.write_one_record("Experiment_description", self.experiment.get_experiment_description_record())
        self.database.write_one_record(
            "Search_space", get_search_space_record(self.experiment.search_space, self.experiment.unique_id)
        )
        self.experiment.send_state_to_db()

        self.sub.send('experiment', 'description',
                      global_config=self.experiment.description["General"],
                      experiment_description=self.experiment.description,
                      searchspace_description=self.experiment.search_space.serialize(True)
                      )
        self.logger.debug("Experiment description and global configuration sent to the API.")

        # Create and launch Stop Condition services in separate threads.
        launch_stop_condition_threads(self.experiment.unique_id)

        # Instantiate client for Worker Service, establish connection.
        self.wsc_client = WSClient(
            self.experiment.description["TaskConfiguration"],
            os.getenv("BRISE_EVENT_SERVICE_HOST"),
            int(os.getenv("BRISE_EVENT_SERVICE_AMQP_PORT"))
        )

        # Initialize Repeater - encapsulate Configuration evaluation process to avoid results fluctuations.
        # (achieved by multiple Configuration evaluations on Workers - Tasks)
        RepeaterOrchestration(self.experiment)

        self.predictor: Predictor = Predictor(
            self.experiment.unique_id, self.experiment.description, self.experiment.search_space
        )

        self.consume_channel.basic_consume(queue='default_configuration_results_queue', auto_ack=True,
                                           on_message_callback=self.get_default_configurations_results)
        self.consume_channel.basic_consume(queue='configurations_results_queue', auto_ack=True,
                                           on_message_callback=self.get_configurations_results)
        self.consume_channel.basic_consume(queue='stop_experiment_queue', auto_ack=True,
                                           on_message_callback=self.stop)
        self.consume_channel.basic_consume(queue="get_new_configuration_queue", auto_ack=True,
                                           on_message_callback=self.send_new_configurations_to_measure)

        self.default_config_handler = get_default_config_handler(self.experiment)
        temp_msg = "Measuring default Configuration."
        self.logger.info(temp_msg)
        self.sub.send('log', 'info', message=temp_msg)
        default_parameters = self.experiment.search_space.generate_default()
        default_configuration = Configuration(default_parameters, Configuration.Type.DEFAULT, self.experiment.unique_id)
        default_configuration.experiment_id = self.experiment.unique_id
        dictionary_dump = {"configuration": default_configuration.to_json()}
        body = json.dumps(dictionary_dump)

        self.consume_channel.basic_publish(exchange='',
                                           routing_key='measure_new_configuration_queue',
                                           body=body)
        # listen all queues with responses until the _is_interrupted flag is False
        try:
            while not self._is_interrupted:
                self.consume_channel.connection.process_data_events(time_limit=1)  # 1 second
        finally:
            if self.connection.is_open:
                self.connection.close()

    def get_default_configurations_results(self, ch, method, properties, body):
        """
        Callback function for the result of default configuration
        :param ch: pika.Channel
        :param method:  pika.spec.Basic.GetOk
        :param properties: pika.spec.BasicProperties
        :param body: result of measuring default configuration in bytes format
        """
        default_configuration = Configuration.from_json(body.decode())
        if default_configuration.status == Configuration.Status.BAD:
            new_default_values = self.default_config_handler.get_new_default_config()
            if new_default_values:
                config = Configuration(
                    new_default_values, Configuration.Type.FROM_SELECTOR, self.experiment.unique_id)
                temp_msg = "New default configuration sampled."
                self.logger.info(temp_msg)
                self.sub.send('log', 'info', message=temp_msg)
                self.consume_channel.basic_publish(exchange='',
                                                   routing_key='measure_new_configuration_queue',
                                                   body=json.dumps({"configuration": config.to_json()}))
            else:
                self.logger.error("The specified default configuration is broken.")
                self.stop()
                self.sub.send('log', 'info', message="The specified default configuration is broken.")
                return
        if self.experiment.is_configuration_evaluated(default_configuration):
            self.experiment.default_configuration = default_configuration
            self.database.update_record("Search_space", {"Exp_unique_ID": self.experiment.unique_id},
                                        {"Default_configuration": default_configuration.get_configuration_record()})
            self.database.update_record("Search_space", {"Exp_unique_ID": self.experiment.unique_id},
                                        {"SearchspaceObject": pickle.dumps(self.experiment.search_space)})

            temp_msg = f"Evaluated Default Configuration: {default_configuration}"
            self.logger.info(temp_msg)
            self.sub.send('log', 'info', message=temp_msg)

            # starting main work: building model and choosing configuration for measuring
            self.consume_channel.basic_publish(exchange='',
                                               routing_key='get_worker_capacity_queue',
                                               body='')

    def get_configurations_results(self, ch, method, properties, body):
        """
        Callback function for the result of all Configurations except Default
        :param ch: pika.Channel
        :param method:  pika.spec.Basic.GetOk
        :param properties: pika.spec.BasicProperties
        :param body: result of measuring any configuration except default in bytes format
        """
        with self.conf_lock:  # To be sure, that no Configuration will be added after satisfying all Stop Conditions.
            configuration = Configuration.from_json(body.decode())
            if not self._is_interrupted and self.experiment.is_configuration_evaluated(configuration):
                self.experiment.try_add_configuration(configuration)
                temp_msg = "-- New Configuration was evaluated. Building Target System model."
                self.logger.info(temp_msg)
                self.sub.send('log', 'info', message=temp_msg)
                self.consume_channel.basic_publish(exchange='',
                                                   routing_key='get_worker_capacity_queue',
                                                   body='')

    def send_new_configurations_to_measure(self, ch, method, properties, body):
        """
        This callback function will be triggered on arrival of ONE measured Configuration.
        When there is new measured Configuration, following steps should be done:

            -   update and validate models;

            -   pick either by model, or by selection algorithm new Configuration(s) for evaluation;
                Note: The amount of new Configurations are:
                - 0 if number of available Worker nodes decreased;
                - 1 if number of available Workers did not change;
                - N + 1 if number of available Worker increased by N;

            -   send new Configuration to Repeater for evaluation.
        """

        needed_configs = json.loads(body.decode()).get("worker_capacity", 1)
        for _ in range(needed_configs):
            config = self.predictor.predict(self.experiment.measured_configurations)
            if config not in self.experiment.evaluated_configurations:
                temp_msg = f"Model predicted {config}."
            else:
                while config in self.experiment.evaluated_configurations and not self._is_interrupted:
                    if len(self.experiment.evaluated_configurations) >= self.experiment.search_space.get_size():
                        msg = "Entire Search Space was evaluated. Shutting down."
                        self.logger.warning(msg)
                        self.consume_channel.basic_publish(exchange='', routing_key='stop_experiment_queue', body=msg)
                        break

                    new_parameter_values = OrderedDict()
                    while not self.experiment.search_space.validate(new_parameter_values, is_recursive=True):
                        self.experiment.search_space.generate(new_parameter_values)
                    config = Configuration(
                        new_parameter_values, Configuration.Type.FROM_SELECTOR, self.experiment.unique_id
                    )
                temp_msg = f"Fully randomly sampled {config}."

            self.logger.info(temp_msg)
            self.sub.send('log', 'info', message=temp_msg)
            self.consume_channel.basic_publish(exchange='',
                                               routing_key='measure_new_configuration_queue',
                                               body=json.dumps({"configuration": config.to_json()}))

    def stop(self, ch=None, method=None, properties=None, body=None):
        """
        The function for stop main thread externally (e.g. from front-end)
        """
        with self.conf_lock:
            self.consume_channel.basic_publish(exchange='brise_termination_sender', routing_key='', body='')
            self.sub.send('log', 'info', message=f"Terminating experiment. Reason: {body}")
            self._state = self.State.SHUTTING_DOWN
            self._is_interrupted = True
            optimal_configuration = self.experiment.get_final_report_and_result()
            self._state = self.State.IDLE
            return optimal_configuration

    def get_state(self):
        return self._state


def run(experiment_setup=None):
    main = MainThread(experiment_setup)
    main.start()
    main.join()


if __name__ == "__main__":
    run()
