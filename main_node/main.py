__doc__ = """
Main module for running BRISE configuration balancing."""

import json
import logging
import os
import pickle
import threading
from enum import Enum
from sys import argv
from warnings import filterwarnings

import pika
from configuration_selection.configuration_selection import ConfigurationSelection
from default_config_handler.default_configuration_handler_orchestrator import DefaultConfigHandlerOrchestrator
from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from core_entities.search_space import Hyperparameter, get_search_space_record

from logger.default_logger import BRISELogConfigurator
from repeater.repeater_selector import RepeaterOrchestration
from stop_condition.stop_condition_selector import (
    launch_stop_condition_threads
)
from tools.front_API import API
from tools.initial_config import load_experiment_setup

from tools.mongo_dao import MongoDB
from WorkerServiceClient.WSClient_events import WSClient

logging.getLogger("pika").setLevel(logging.WARNING)
filterwarnings("ignore")  # disable warnings for demonstration.


class MainThread(threading.Thread):
    """
    This class runs Main functionality in a separate thread,
    connected to the `default_configuration_results_exchange` and `configurations results queue` as a consumer.
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

        # TODO: Description for the fields?
        self.experiment: Experiment = None
        self.connection: pika.BlockingConnection = None
        self.consume_channel = None
        self.wsc_client: WSClient = None
        self.database: MongoDB = None
        self.is_transfer_enabled = False

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
            experiment_description = self.experiment_setup["metric_description"]
            search_space = self.experiment_setup["search_space"]

        os.makedirs("./Results/", exist_ok=True)  # FIXME remove hardcode

        # Initializing instance of Experiment - main data holder.
        self.experiment = Experiment(experiment_description, search_space)
        # self.experiment_id = self.experiment.unique_id
        # search_space.experiment_id = self.experiment_id
        Configuration.set_task_config(self.experiment.description["Context"]["TaskConfiguration"])

        # initialize connection to rabbitmq service
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                os.getenv("BRISE_EVENT_SERVICE_HOST"),
                int(os.getenv("BRISE_EVENT_SERVICE_AMQP_PORT"))
            )
        )
        self.consume_channel = self.connection.channel()
        self.create_and_bind_queues()
        self.consume_channel.basic_consume(queue='default_configuration_results_exchange' + self.experiment.unique_id, auto_ack=True,
                                           on_message_callback=self.get_default_configurations_results)
        self.consume_channel.basic_consume(queue='configurations_results_exchange' + self.experiment.unique_id, auto_ack=True,
                                           on_message_callback=self.get_configurations_results)
        self.consume_channel.basic_consume(queue='stop_experiment_exchange' + self.experiment.unique_id, auto_ack=True,
                                           on_message_callback=self.stop)
        self.consume_channel.basic_consume(queue="experiment_api_exchange" + self.experiment.unique_id, auto_ack=True,
                                           on_message_callback=self.experiment_api)
        self.consume_channel.basic_consume(queue="logging_exchange" + self.experiment.unique_id, auto_ack=True,
                                           on_message_callback=self.logging_api)
        self.consume_channel.basic_consume(queue='stop_experiment_queue', auto_ack=True,
                                           on_message_callback=self.stop)

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
                      global_config={},  # FIXME Stub. When front-end is enabled again
                      experiment_description=self.experiment.description,
                      searchspace_description=self.experiment.search_space.serialize()
                      )
        self.logger.debug("Experiment description and global configuration sent to the API.")

        # Create and launch Stop Condition services in separate threads.
        launch_stop_condition_threads(self.experiment.unique_id)

        # Instantiate client for Worker Service, establish connection.
        # TODO: change this to event-based communication.
        #  (https://github.com/dpukhkaiev/BRISEv2/pull/145#discussion_r440165389)
        self.wsc_client = WSClient(self.experiment.unique_id)

        # Initialize Repetition Manager - a mechanism for handling nondeterminism.
        RepeaterOrchestration(experiment_id=self.experiment.unique_id, experiment=self.experiment)

        ConfigurationSelection(self.experiment)

        dch_o = DefaultConfigHandlerOrchestrator()
        default_config_handler = dch_o.get_default_configuration_handler(experiment=self.experiment)
        temp_msg = "Measuring default Configuration."
        self.logger.info(temp_msg)
        self.sub.send('log', 'info', message=temp_msg)
        default_configuration = default_config_handler.get_default_configuration()
        self.experiment.add_evaluated_configuration_to_experiment(default_configuration)

        dictionary_dump = {"configuration": default_configuration.to_json()}
        body = json.dumps(dictionary_dump)

        self.consume_channel.basic_publish(exchange='measure_new_configuration_exchange',
                                           routing_key=self.experiment.unique_id,
                                           body=body)
        # listen all queues with responses until the _is_interrupted flag is False
        try:
            while not self._is_interrupted:
                self.consume_channel.connection.process_data_events(time_limit=1)  # 1 second
        finally:
            self.logger.info(f"{__name__} is shutting down.")
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
        self.logger.info("Got DEFAULT config from Repeater")

        if default_configuration.status['measured']:
            self.logger.info("Configuration is measured")
            self.experiment.default_configuration = default_configuration
            self.database.update_record("Search_space", {"Exp_unique_ID": self.experiment.unique_id},
                                        {"Default_configuration": default_configuration.get_configuration_record()})
            self.database.update_record("Search_space", {"Exp_unique_ID": self.experiment.unique_id},
                                        {"SearchspaceObject": pickle.dumps(self.experiment.search_space)})

            temp_msg = f"Evaluated Default Configuration: {default_configuration}"
            self.logger.info(temp_msg)
            self.sub.send('log', 'info', message=temp_msg)

            # starting main work: building model and choosing configuration for measuring
            self.consume_channel.basic_publish(exchange='get_worker_capacity_exchange',
                                               routing_key=self.experiment.unique_id,
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
            self.logger.info("Got REGULAR config from Repeater")
            if not self._is_interrupted and configuration.status['measured']:
                self.experiment.add_configuration(configuration)
                temp_msg = "-- New Configuration was evaluated. Building Target System model."
                self.logger.info(temp_msg)
                self.sub.send('log', 'info', message=temp_msg)
                self.consume_channel.basic_publish(exchange='get_worker_capacity_exchange',
                                                   routing_key=self.experiment.unique_id,
                                                   body='')

    def experiment_api(self, ch=None, method=None, properties=None, body=None):
        dictionary_dump = json.loads(body.decode())
        getattr(self.experiment, dictionary_dump)()

    def logging_api(self, ch=None, method=None, properties=None, body=None):
        dictionary_dump = json.loads(body.decode())
        self.logger.info(dictionary_dump)

    def stop(self, ch=None, method=None, properties=None, body=None):
        """
        The function for stop main thread externally (e.g. from front-end)
        """
        with self.conf_lock:
            self.sub.send('log', 'info', message=f"Terminating experiment. Reason: {body}")
            self.logger.info(f"Terminating experiment. Reason: {body}")
            self._state = self.State.SHUTTING_DOWN
            self._is_interrupted = True
            optimal_configuration = self.experiment.get_final_report_and_result()
            self._state = self.State.IDLE
            self.consume_channel.basic_publish(exchange='experiment_termination_exchange',
                                               routing_key=self.experiment.unique_id,
                                               body='')
            return optimal_configuration

    def get_state(self):
        return self._state

    def create_and_bind_queues(self):
        """
        The method to create a set of queues to provide communication for this experiment
        """
        self.exchanges = ['experiment_termination_exchange', 'task_result_exchange', 'measurement_results_exchange',
                          'default_configuration_results_exchange', 'configurations_results_exchange',
                          'stop_experiment_exchange', 'check_stop_condition_expression_exchange', 'logging_exchange',
                          'get_worker_capacity_exchange', 'get_new_configuration_exchange',
                          'measure_new_configuration_exchange', 'process_tasks_exchange', 'experiment_api_exchange']
        for exchange in self.exchanges:
            queue_name = exchange + self.experiment.unique_id
            result = self.consume_channel.queue_declare(queue=queue_name)
            queue_name = result.method.queue
            self.consume_channel.queue_bind(queue=queue_name, exchange=exchange, routing_key=self.experiment.unique_id)

    def unbind_and_delete_queues(self):
        """
        The method to remove all created queues after the experiment stop
        """
        for exchange in self.exchanges:
            queue_name = exchange + self.experiment.unique_id
            self.consume_channel.queue_unbind(queue=queue_name, exchange=exchange, routing_key=self.experiment.unique_id)
            self.consume_channel.queue_delete(queue=queue_name)


def run(experiment_setup=None):
    main = MainThread(experiment_setup)
    main.start()
    main.join()


if __name__ == "__main__":
    run()
