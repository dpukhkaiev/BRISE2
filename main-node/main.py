__doc__ = """
Main module for running BRISE configuration balancing."""

import logging
import pika
import threading

from warnings import filterwarnings
filterwarnings("ignore")    # disable warnings for demonstration.

from WorkerServiceClient.WSClient_events import WSClient
from model.model_selection import get_model
from repeater.repeater import Repeater
from tools.initial_config import load_global_config, load_experiment_setup, validate_experiment_description
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

    def __init__(self, experiment_setup=None):
        """
        The function for initializing main thread
        :param experiment_setup: fully initialized experiment, r.g from a POST request
        """
        super(MainThread, self).__init__()
        self.global_config = load_global_config()
        self._is_interrupted = False
        self.conf_lock = threading.Lock()
        # initialize connection to rabbitmq service
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.global_config["EventService"]["Address"],
                port=self.global_config["EventService"]["Port"]))
        self.consume_channel = self.connection.channel()

        self.sub = API()  # subscribers
        if __name__ == "__main__":
            self.logger = BRISELogConfigurator().get_logger(__name__)
        else:
            self.logger = logging.getLogger(__name__)

        self.logger.info("Starting BRISE")

        self.sub.send('log', 'info', message="Starting BRISE")

        if not experiment_setup:
            default_ed_file = './Resources/EnergyExperiment.json'
            log_msg = "The Experiment Setup was not provided. The default one will be executed: %s" % default_ed_file
            self.logger.warning(log_msg)
            self.sub.send('log', 'warning', message=log_msg)
            experiment_description, search_space = load_experiment_setup(default_ed_file)
        else:
            experiment_description = experiment_setup["experiment_description"]
            search_space = experiment_setup["search_space"]

        validate_experiment_description(experiment_description)

        self.experiment = Experiment(experiment_description, search_space)
        Configuration.set_task_config(self.experiment.description["TaskConfiguration"])

        self.sub.send('experiment', 'description',
                      global_config=self.global_config,
                      experiment_description=self.experiment.description,
                      searchspace_description=self.experiment.search_space.generate_searchspace_description()
                      )
        self.logger.debug("Experiment description and global configuration sent to the API.")

        # sc group initialization which parameters could be defined without statistic data usage
        self.prior_stop_condition = get_stop_condition(self.experiment, True)

        # Creating instance of selector algorithm, according to specified in experiment description type.
        self.selector = get_selector(experiment=self.experiment)

        # Instantiate client for Worker Service, establish connection.
        # TODO: LOGFILE parameter should be chosen according to the name of file, that provides Experiment description
        # (task.json)

        self.worker_service_client = WSClient(self.experiment.description["TaskConfiguration"],
                                              self.global_config["EventService"]["Address"],
                                              self.global_config["EventService"]["Port"],
                                              logfile='%s%s_WSClient.csv' % (self.global_config['results_storage'],
                                                                             self.experiment.get_name()))

        # Creating runner for experiments that will repeat the configuration measurement to avoid fluctuations.
        self.repeater = Repeater(self.worker_service_client, self.experiment)

        self.default_config_handler = get_default_config_handler(self.experiment)

    def run(self):
        """
        Point of entry to the main functionality, measuring default configuration,
        and starting listening of queues with responses
        """
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

            temp_msg = "Results of measuring default value: %s" % self.experiment.search_space.get_default_configuration().get_average_result()
            self.logger.info(temp_msg)
            self.sub.send('log', 'info', message=temp_msg)

            self.model = get_model(experiment=self.experiment,
                                   log_file_name="%s%s%s_model.txt" % (self.global_config['results_storage'],
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
        Callback function for the result of any configuration except default
        :param ch: pika.Channel
        :param method:  pika.spec.Basic.GetOk
        :param properties: pika.spec.BasicProperties
        :param body: result of measuring any configuration except default in bytes format
        :return:optimal configuration
        """
        with self.conf_lock:  # for be sure that any of configurations won't be added after finding the near-optimal configuration
            configuration = Configuration.from_json(body.decode())
            if not self._is_interrupted and self.experiment.is_configuration_evaluated(configuration):
                self.experiment.try_add_configurations([configuration])
                self.selector.disable_configurations([configuration])
                finish = self.posterior_stop_condition.validate_conditions()
                if not finish:
                    try:
                        finish = self.prior_stop_condition.validate_conditions()
                    except Exception as e:
                        self.logger.error("Priori group SC was terminated by Exception: %s." % type(e), exc_info=e)
                if finish:
                    self.stop()  # stop all internal thread after getting the optimal configuration
                    self.sub.send('log', 'info', message="Solution validation success!")
                    optimal_configuration = self.experiment.get_final_report_and_result(self.repeater)
                    return optimal_configuration
                else:
                    temp_msg = "-- New Configuration(s) was(were) measured. Currently were evaluated " \
                               f"{len(self.model.measured_configurations)} of {self.experiment.search_space.get_search_space_size()}" \
                               " Configurations. Building Target System model.\n"
                    self.logger.info(temp_msg)
                    self.sub.send('log', 'info', message=temp_msg)

                    # repeat work() function until the near-optimal configuration will be found
                    self.send_new_configurations_to_measure()

    def send_new_configurations_to_measure(self):
        """
        The function for building model and choosing configuration for measuring
        """
        model_built = self.model.update_data(self.experiment.measured_configurations).build_model()
        for n in range(self.worker_service_client.get_number_of_needed_configurations()):  # for dynamic parallelization
            if model_built and self.model.validate_model():
                i = 1
                while True:
                    predicted_configurations = self.model.predict_next_configurations(i)
                    is_unique_configuration = False
                    for conf in predicted_configurations:
                        if conf.status == Configuration.Status.NEW:
                            self.repeater.measure_configurations([conf])
                            is_unique_configuration = True
                            break
                    if is_unique_configuration:
                        break
                    else:
                        i += 1
                temp_msg = "Predicted following Configuration->Quality pairs: %s" \
                           % list((str(c) + "->" + str(c.predicted_result) for c in predicted_configurations))
                self.logger.info(temp_msg)
                self.sub.send('log', 'info', message=temp_msg)
            else:
                while True:
                    configs_from_selector = self.selector.get_next_configuration()
                    if self.experiment.get_any_configuration_by_parameters(configs_from_selector.parameters) is None:
                        self.repeater.measure_configurations([configs_from_selector])
                        break

    def stop(self):
        """
        The function for stop main thread
        """
        self._is_interrupted = True
        self.worker_service_client.stop()
        self.repeater.stop()


def run(experiment_setup=None):
    main = MainThread(experiment_setup)
    main.start()
    main.join()


if __name__ == "__main__":
    run()
