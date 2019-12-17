__doc__ = """
Main module for running BRISE configuration balancing."""

import logging
import pika
import threading
from enum import Enum
from sys import argv

from warnings import filterwarnings

filterwarnings("ignore")  # disable warnings for demonstration.

from WorkerServiceClient.WSClient_events import WSClient
from model.model_selection import get_model
from repeater.repeater import Repeater
from tools.initial_config import load_experiment_setup, validate_experiment_description
from tools.front_API import API
from selection.selection_algorithms import get_selector
from logger.default_logger import BRISELogConfigurator
from stop_condition.stop_condition_selector import get_stop_condition
from core_entities.experiment import Experiment
from core_entities.configuration import Configuration
from default_config_handler.default_config_handler_selector import get_default_config_handler
from default_config_handler.default_config_handler import DefaultConfigurationHandler


class MainThread(threading.Thread):
    """
    This class runs Main functionality in a separate thread,
    connected to the `default_configuration_results_queue` and `configurations results queue` as a consumer.
    """

    class State(int, Enum):
        RUNNING = 0
        SHUTTING_DOWN = 1
        IDLE = 2

    def __init__(self, experiment_setup=None):
        """
        The function for initializing main thread
        :param experiment_setup: fully initialized experiment, r.g from a POST request
        """
        super(MainThread, self).__init__()
        self._is_interrupted = False
        self.conf_lock = threading.Lock()
        self._state = self.State.IDLE
        self.experiment_setup = experiment_setup

    def run(self):
        """
        Entry point to the main node functionality - measuring default Configuration.
        When the default Configuration finishes it's evaluation, the first bunch of Configurations will be
        sampled for evaluation (respectively, the queues for Configuration measurement results initializes).
        """
        self.sub = API()  # subscribers

        if __name__ == "__main__":
            self.logger = BRISELogConfigurator().get_logger(__name__)
        else:
            self.logger = logging.getLogger(__name__)

        self._state = self.State.RUNNING
        self.logger.info("Starting BRISE")

        self.sub.send('log', 'info', message="Starting BRISE")

        if not self.experiment_setup:
            # Check if main.py running with a specified experiment description file path
            if len(argv) > 1:
                exp_desc_file_path = argv[1]
            else:
                exp_desc_file_path = './Resources/EnergyExperiment.json'
                log_msg = f"The Experiment Setup was not provided and the path to an experiment file was not specified." \
                          f" The default one will be executed: {exp_desc_file_path}"
                self.logger.warning(log_msg)
                self.sub.send('log', 'warning', message=log_msg)
            experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        else:
            experiment_description = self.experiment_setup["experiment_description"]
            search_space = self.experiment_setup["search_space"]

        validate_experiment_description(experiment_description)

        # Initializing instance of Experiment - main data holder.
        self.experiment = Experiment(experiment_description, search_space)
        Configuration.set_task_config(self.experiment.description["TaskConfiguration"])

        # initialize connection to rabbitmq service
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.experiment.description["General"]["EventService"]["Address"],
                port=self.experiment.description["General"]["EventService"]["Port"]))
        self.consume_channel = self.connection.channel()

        self.sub.send('experiment', 'description',
                      global_config=self.experiment.description["General"],
                      experiment_description=self.experiment.description,
                      searchspace_description=self.experiment.search_space.generate_searchspace_description()
                      )
        self.logger.debug("Experiment description and global configuration sent to the API.")

        # Initializing Prior group of Stop Conditions, according to Experiment Description specification.
        self.prior_stop_condition = get_stop_condition(self.experiment, True)

        # Initializing Selector Algorithm, according to Experiment Description specification.
        self.selector = get_selector(experiment=self.experiment)

        # Instantiate client for Worker Service, establish connection.
        # TODO: LOGFILE parameter should be chosen according to the name of file, that provides Experiment description
        # (task.json)

        self.worker_service_client = WSClient(self.experiment.description["TaskConfiguration"],
                                              self.experiment.description["General"]["EventService"]["Address"],
                                              self.experiment.description["General"]["EventService"]["Port"],
                                              logfile='%s%s_WSClient.csv' % (self.experiment.description["General"]['results_storage'],
                                                                             self.experiment.get_name()))

        # Initialize Repeater - encapsulate Configuration evaluation process to avoid results fluctuations.
        # (achieved by multiple Configuration evaluations on Workers - Tasks)
        self.repeater = Repeater(self.worker_service_client, self.experiment)

        self.default_config_handler = get_default_config_handler(self.experiment)
        temp_msg = "Measuring default Configuration."
        self.logger.info(temp_msg)
        self.sub.send('log', 'info', message=temp_msg)
        self.consume_channel.basic_consume(queue='default_configuration_results_queue', auto_ack=True,
                                           on_message_callback=self.get_default_configurations_results)
        self.consume_channel.basic_consume(queue='configurations_results_queue', auto_ack=True,
                                           on_message_callback=self.get_configurations_results)
        default_configuration = self.default_config_handler.get_default_config()

        self.repeater.measure_configurations([default_configuration])
        # listen all queues with responses until the _is_interrupted flag is False
        try:
            while self.consume_channel._consumer_infos:
                self.consume_channel.connection.process_data_events(time_limit=1)  # 1 second
                if self._is_interrupted:
                    if self.connection.is_open:
                        self.connection.close()
                    break
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
        self.selector.disable_configurations([default_configuration])
        if default_configuration.status == Configuration.Status.BAD:
            if type(self.default_config_handler) == DefaultConfigurationHandler:
                self.logger.error("The specified default configuration is broken.")
                self.stop()
                self.sub.send('log', 'info', message="The specified default configuration is broken.")
                return
            default_configuration = self.default_config_handler.get_default_config()
            self.repeater.measure_configurations([default_configuration])
        if self.experiment.is_configuration_evaluated(default_configuration):
            self.experiment.put_default_configuration(default_configuration)

            temp_msg = f"Evaluated Default Configuration: {default_configuration}"
            self.logger.info(temp_msg)
            self.sub.send('log', 'info', message=temp_msg)

            self.model = get_model(experiment=self.experiment,
                                   log_file_name="%s%s%s_model.txt" % (self.experiment.description["General"]['results_storage'],
                                                                       self.experiment.get_name(),
                                                                       self.experiment.description[
                                                                           "ModelConfiguration"][
                                                                           "ModelType"]))
            self.posterior_stop_condition = get_stop_condition(self.experiment, False)
            self.repeater.set_type(self.experiment.description["Repeater"]["Type"])
            # starting main work: building model and choosing configuration for measuring
            self.send_new_configurations_to_measure()

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
                self.selector.disable_configurations([configuration])
                finish = self.posterior_stop_condition.validate_conditions()
                if not finish:
                    try:
                        finish = self.prior_stop_condition.validate_conditions()
                    except Exception as e:
                        self.logger.error("Priori group SC was terminated by Exception: %s." % type(e), exc_info=e)
                if finish:
                    self.stop()  # stop all internal threads
                    self.sub.send('log', 'info', message="Solution validation success!")
                    return
                else:
                    temp_msg = "-- New Configuration was evaluated. Building Target System model."
                    self.logger.info(temp_msg)
                    self.sub.send('log', 'info', message=temp_msg)
                    self.send_new_configurations_to_measure()

    def send_new_configurations_to_measure(self):
        """
        The function for building model and choosing configuration for measuring
        """
        model_built = self.model.update_data(self.experiment.measured_configurations).build_model()
        for n in range(self.worker_service_client.get_number_of_needed_configurations()):  # for dynamic parallelization
            is_model_produce_unique_configuration = False
            if model_built and self.model.validate_model():
                for i in range(5):  # 5 times to try to get unique configuration
                    predicted_configurations = self.model.predict_next_configurations(i + 1)
                    for conf in predicted_configurations:
                        if conf.status == Configuration.Status.NEW:
                            self.repeater.measure_configurations([conf])
                            is_model_produce_unique_configuration = True
                            break
                    temp_msg = "Predicted following Configuration->Quality pairs: %s" \
                               % list((str(c) + "->" + str(c.predicted_result) for c in predicted_configurations))
                    self.logger.info(temp_msg)
                    self.sub.send('log', 'info', message=temp_msg)

                    if is_model_produce_unique_configuration:
                        break
            if not is_model_produce_unique_configuration:
                while True:
                    configs_from_selector = self.selector.get_next_configuration()
                    if self.experiment.get_any_configuration_by_parameters(configs_from_selector.parameters) is None:
                        self.repeater.measure_configurations([configs_from_selector])
                        break

    def get_state(self):
        return self._state

    def stop(self):
        """
        The function for stop main thread externaly (e.g. from front-end)
        """
        self._state = self.State.SHUTTING_DOWN
        self._is_interrupted = True
        self.worker_service_client.stop()
        self.repeater.stop()
        self.experiment.get_final_report_and_result(self.repeater)
        self._state = self.State.IDLE


def run(experiment_setup=None):
    main = MainThread(experiment_setup)
    main.start()
    main.join()


if __name__ == "__main__":
    run()
