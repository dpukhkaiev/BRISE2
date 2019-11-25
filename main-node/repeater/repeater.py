import logging
from enum import Enum

import pika
import pika.exceptions
import json
import threading

from WorkerServiceClient.WSClient_events import WSClient
from tools.front_API import API
from tools.reflective_class_import import reflective_class_import
from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from outliers.outliers_detector_selector import get_outlier_detectors

logging.getLogger("pika").propagate = False


class ConsumerThread(threading.Thread):
    """
    This class runs in a separate thread and handles measurement result from WSClient,
    connected to the `measurement_results_queue` as consumer and recheck measurement by repeater.measure_configurations
    """

    def __init__(self, repeater):
        """
        :param repeater: an instance of repeater object
        """
        super(ConsumerThread, self).__init__()
        self.repeater = repeater
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(repeater.worker_service_client.event_host,
                                                                            repeater.worker_service_client.event_port))

        self.consume_channel = self.connection.channel()
        self._is_interrupted = False

        self.consume_channel.basic_consume(queue='measurement_results_queue', auto_ack=True,
                                           on_message_callback=self.callback_func)

    def callback_func(self, channel, method, properties, body):
        """
        Callback function for the result of measuring
        :param ch: pika.Channel
        :param method:  pika.spec.Basic.GetOk
        :param properties: pika.spec.BasicProperties
        :param body: result of a configurations in bytes format
        """
        result = json.loads(body.decode())
        configuration = Configuration.from_json(result["configuration"])
        tasks_to_send = result["tasks_to_send"]
        tasks_results = result["tasks_results"]
        results_WO_outliers = self.repeater.outlier_detectors.find_outliers_for_taskset(tasks_results,
                                                                                        self.repeater._result_structure,
                                                                                        [configuration],
                                                                                        tasks_to_send)
        # Sending data to API and adding Tasks to Configuration
        for parameters, task in zip(tasks_to_send, results_WO_outliers):
            if configuration.parameters == parameters:
                if configuration.is_valid_task(task):
                    configuration.add_tasks(task)
                else:
                    configuration.increase_failed_tasks_number()

            API().send('new', 'task', configurations=[parameters], results=[task])

        # Evaluating configuration
        self.repeater.measure_configurations([configuration])

    def run(self):
        """
        Point of entry to tasks results consumers functionality,
        listening of queue with measurement result
        """
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

    def stop(self):
        self._is_interrupted = True


class Repeater:
    def __init__(self, worker_service_client: WSClient, experiment):

        self.worker_service_client = worker_service_client
        self.performed_measurements = 0
        self.repeater_parameters = experiment.description["Repeater"]["Parameters"]
        self.outlier_detectors = get_outlier_detectors(experiment.get_outlier_detectors_parameters())
        self.logger = logging.getLogger(__name__)
        self._result_structure = experiment.description["TaskConfiguration"]["ResultStructure"]
        self.configurations = []
        self.experiment = experiment

        self._type = None
        self.set_type("Default")  # Default Configuration will be measured precisely with Default Repeater Type.
        self.listen_thread = ConsumerThread(self)
        self.listen_thread.start()

    def stop(self):
        self.listen_thread.stop()
        self.listen_thread.join()

    def evaluation_by_type(self, current_configuration: Configuration):
        """
        Forwards a call to specific Repeater Type to evaluate if Configuration was measured precisely.
        :param current_configuration: instance of Configuration class.
        :returns: int Number of measurements of Configuration which need to be performed, EvaluationStatus
        """

        if self._type is None:
            raise TypeError("Repeater evaluation Type was not selected!")
        else:
            if current_configuration.status == Configuration.Status.NEW:
                number_of_measurements = self._type.evaluate(current_configuration=current_configuration,
                                                             experiment=self.experiment)
                current_configuration.status = Configuration.Status.EVALUATED
                if self.experiment.try_add_configurations([current_configuration]) or \
                        current_configuration.type == Configuration.Type.DEFAULT:  # for repeating default configuration
                    return number_of_measurements
                else:
                    current_configuration.status = Configuration.Status.EVALUATED
                    return 0
            else:
                if current_configuration.get_average_result() is not []:
                    number_of_measurements = self._type.evaluate(current_configuration=current_configuration,
                                                                 experiment=self.experiment)
                    if number_of_measurements > 0:
                        current_configuration.status = Configuration.Status.REPEATED_MEASURING
                        return number_of_measurements
                    else:
                        current_configuration.status = Configuration.Status.MEASURED
                        return 0
                else:
                    current_configuration.Status = Configuration.Status.EVALUATED
                    return 0

    def set_type(self, repeater_type: str):
        """
            This method change current Type of Repeater.
        :param repeater_type: String.
                The name of Repeater Type with desired evaluation function for repeater.
                Possible values - "Default", "Student Deviation".
                "Default" - adds fixed number of Tasks to each Configuration, no evaluation performed.
                "Student deviation" - adds Tasks until result of Configuration measurement reaches appropriate accuracy,
                the quality of each configuration (how it close to currently best found Configuration) and deviation of
                each experiment are taken into account.
        :return: None.
        """
        evaluation_class = reflective_class_import(class_name=repeater_type, folder_path="repeater")
        self._type = evaluation_class(self.repeater_parameters)

    def measure_configurations(self, configurations: list):
        """
        Evaluates the Target System using specific Configuration while results of Evaluation will not be precise.
        :param configurations: list of Configurations that are needed to be measured.
        :returns: list of Configurations that were evaluated
        """

        # Removing previous measurements

        result = []  # used for tests only
        needed_tasks_count = 0
        # Creating holders for current measurements
        for configuration in configurations:
            current_measurement = {}
            # Evaluating each Configuration in configurations list
            if configuration.number_of_failed_tasks <= self.repeater_parameters['MaxFailedTasksPerConfiguration']:
                needed_tasks_count = self.evaluation_by_type(configuration)
            else:
                needed_tasks_count = 0
                configuration.status = Configuration.Status.BAD
                if len(configuration.get_tasks()) == 0:
                    self.experiment.increment_bad_configuration_number()
                    configuration.disable_configuration()

            current_measurement[str(configuration.parameters)] = {'parameters': configuration.parameters,
                                                                  'needed_tasks_count': needed_tasks_count,
                                                                  'Finished': False}

            if needed_tasks_count == 0:
                current_measurement[str(configuration.parameters)]['Finished'] = True
                current_measurement[str(configuration.parameters)]['Results'] = configuration.get_average_result()

            tasks_to_send = []
            for point in current_measurement.keys():
                if not current_measurement[point]['Finished']:
                    for i in range(current_measurement[point]['needed_tasks_count']):
                        tasks_to_send.append(current_measurement[point]['parameters'])
                        self.performed_measurements += 1

            if configuration.status == Configuration.Status.MEASURED or \
                    configuration.status == Configuration.Status.BAD:
                with pika.BlockingConnection(
                        pika.ConnectionParameters(host=self.worker_service_client.event_host,
                                                  port=self.worker_service_client.event_port)) as connection:
                    with connection.channel() as channel:
                        try:
                            if configuration.type == Configuration.Type.DEFAULT:
                                channel.basic_publish(exchange='',
                                                      routing_key='default_configuration_results_queue',
                                                      body=configuration.to_json())
                            elif configuration.type == Configuration.Type.PREDICTED or \
                                    configuration.type == Configuration.Type.FROM_SELECTOR:
                                channel.basic_publish(exchange='',
                                                      routing_key='configurations_results_queue',
                                                      body=configuration.to_json())
                        except pika.exceptions.ChannelWrongStateError as err:
                            if not channel.is_open:
                                self.logger.warning("Attempt to send a message after closing the connection")
                            else:
                                raise err
            elif configuration.status == Configuration.Status.EVALUATED or \
                    configuration.status == Configuration.Status.REPEATED_MEASURING:
                result = self.worker_service_client.work(configuration.to_json(), tasks_to_send)
        return result
