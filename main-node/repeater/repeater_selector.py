import logging
import pika
import json
import threading
import os
from abc import ABC, abstractmethod

from tools.front_API import API
from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from repeater.results_check.outliers_detection.outliers_detector_selector import get_outlier_detectors
from repeater.results_check.task_errors_check import error_check
from tools.mongo_dao import MongoDB
from collections.abc import Mapping
from tools.reflective_class_import import reflective_class_import
logging.getLogger("pika").propagate = False


class RepeaterOrchestration():
    """
    This class runs repeater creation process, task preprocessing (errors, outliers check)
    and configuration status management.
    """

    def __init__(self, experiment: Experiment):

        self.logger = logging.getLogger(__name__)
        self.experiment = experiment
        self.performed_measurements = 0
        self.event_host = os.getenv("BRISE_EVENT_SERVICE_HOST")
        self.event_port = os.getenv("BRISE_EVENT_SERVICE_AMQP_PORT")
        self.repeater_parameters = self.experiment.description["Repeater"]["Parameters"]
        self._objectives = self.experiment.description["TaskConfiguration"]["Objectives"]
        self._objectives_data_types = self.experiment.description["TaskConfiguration"]["ObjectivesDataTypes"]
        self._expected_values_range = self.experiment.description["TaskConfiguration"]["ExpectedValuesRange"]
        self.database = MongoDB(os.getenv("BRISE_DATABASE_HOST"), 
                        os.getenv("BRISE_DATABASE_PORT"), 
                        os.getenv("BRISE_DATABASE_NAME"),
                        os.getenv("BRISE_DATABASE_USER"),
                        os.getenv("BRISE_DATABASE_PASS"))
        if self.experiment.description["OutliersDetection"]["isEnabled"]:
            self.outlier_detectors = get_outlier_detectors(experiment.get_outlier_detectors_parameters())
        else:
            self.logger.info("Outliers detection module is disabled")
        self._type = self.get_repeater(True)
        if os.environ.get('TEST_MODE') != 'UNIT_TEST':
            self.listen_thread = EventServiceConnection(self)
            self.listen_thread.start()

    def get_repeater(self, is_default_configuration: bool=False):
        """
        This method selects concrete instance of the Repeater class, for default configuration Quantity-based repeater
        should be used
        :param experiment: the instance of Experiment class
        :param is_default_configuration: is Repeater called to measure default configuration? default=False
        :return instance of a concrete Repeater
        """
        logger = logging.getLogger(__name__)
        parameters = self.experiment.get_repeater_parameters()

        if not is_default_configuration:
            repeater_class = reflective_class_import(class_name=parameters["Type"], folder_path="repeater")
        else:
            repeater_class = reflective_class_import(class_name="Quantity-based", folder_path="repeater")

        msg = parameters["Type"]
        logger.debug(f"Assigned {msg} Repetition Management strategy.")
        return repeater_class(self.experiment, parameters)

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
                if self.experiment.try_add_configuration(current_configuration) or \
                        current_configuration.type == Configuration.Type.DEFAULT:  # for repeating default configuration
                    return number_of_measurements
                else:
                    current_configuration.status = Configuration.Status.EVALUATED
                    return 0
            else:
                if current_configuration.results:
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

    def measure_configurations(self, channel, method, properties, body):
        """
        Callback function for the result of measuring
        :param ch: pika.Channel
        :param method:  pika.spec.Basic.GetOk
        :param properties: pika.spec.BasicProperties
        :param body: result of a configurations in bytes format
        """
        if os.environ.get('TEST_MODE') == 'UNIT_TEST':
            result = json.loads(body)
        else:
            result = json.loads(body.decode())
        configuration = Configuration.from_json(result["configuration"])
        if configuration.status != Configuration.Status.NEW and os.environ.get('TEST_MODE') != 'UNIT_TEST':
            tasks_to_send = result["tasks_to_send"]
            tasks_results = result["tasks_results"]
            for index, objective in enumerate(self._objectives):
                tasks_results = error_check(tasks_results,
                                            objective,
                                            self._expected_values_range[index],
                                            self._objectives_data_types[index])
            if self.experiment.description["OutliersDetection"]["isEnabled"]:
                tasks_results = self.outlier_detectors.find_outliers_for_taskset(tasks_results,
                                                                                 self._objectives,
                                                                                 [configuration],
                                                                                 tasks_to_send)

            # Sending data to API and adding Tasks to Configuration
            for parameters, task in zip(tasks_to_send, tasks_results):
                if configuration.parameters == parameters:
                    if configuration.is_valid_task(task):
                        configuration.add_task(task)
                        if os.environ.get('TEST_MODE') != 'UNIT_TEST':
                            self.database.write_one_record("Tasks", configuration.get_task_record(task))
                    else:
                        configuration.increase_failed_tasks_number()

                API().send('new', 'task', configurations=[parameters], results=[task])

        # Evaluating configuration
        if configuration.number_of_failed_tasks <= self.repeater_parameters['MaxFailedTasksPerConfiguration']:
            needed_tasks_count = self.evaluation_by_type(configuration)
        else:
            needed_tasks_count = 0
            configuration.status = Configuration.Status.BAD
            if len(configuration.get_tasks()) == 0:
                self.experiment.increment_bad_configuration_number()
                configuration.disable_configuration()
        current_measurement = {
            str(configuration.parameters): {
                'parameters': configuration.parameters,
                'needed_tasks_count': needed_tasks_count,
                'Finished': False
            }
        }

        if needed_tasks_count == 0:
            current_measurement[str(configuration.parameters)]['Finished'] = True
            current_measurement[str(configuration.parameters)]['Results'] = configuration.results

        tasks_to_send = []
        for point in current_measurement.keys():
            if not current_measurement[point]['Finished']:
                for i in range(current_measurement[point]['needed_tasks_count']):
                    tasks_to_send.append(current_measurement[point]['parameters'])
                    self.performed_measurements += 1
                    if os.environ.get('TEST_MODE') != 'UNIT_TEST':
                        self.database.write_one_record("Repeater_measurements", self.get_repeater_measurements_record())

        if os.environ.get('TEST_MODE') == 'UNIT_TEST':
            return configuration, needed_tasks_count

        elif configuration.status == Configuration.Status.MEASURED or configuration.status == Configuration.Status.BAD:

            conn_params = pika.ConnectionParameters(host=self.event_host, port=int(self.event_port))
            with pika.BlockingConnection(conn_params) as connection:
                with connection.channel() as channel:
                    try:
                        if configuration.type == Configuration.Type.DEFAULT:
                            self._type = self.get_repeater()
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

            conn_params = pika.ConnectionParameters(host=self.event_host, port=int(self.event_port))
            with pika.BlockingConnection(conn_params) as connection:
                with connection.channel() as channel:
                    body = json.dumps({"configuration": configuration.to_json(), "tasks": tasks_to_send})
                    channel.basic_publish(exchange='', routing_key='process_tasks_queue', body=body)

    def get_repeater_measurements_record(self) -> Mapping:
        '''
        The helper method that formats current repeater measurements' to be stored as a record in a Database
        :return: Mapping. Field names of the database collection with respective information
        '''
        record = {}
        record["Exp_unique_ID"] = self.experiment.unique_id
        record["Performed_measurements"] = self.performed_measurements
        return record


class EventServiceConnection(threading.Thread):
    """
    This class runs in a separate thread and handles measurement result from WSClient,
    connected to the `measurement_results_queue` as consumer and recheck measurement by repeater.measure_configurations
    """

    def __init__(self, orchestrator):
        """
        :param orchestrator: an instance of Repeater Orchestrator object
        """
        super(EventServiceConnection, self).__init__()
        self.orchestrator: RepeaterOrchestration = orchestrator
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(orchestrator.event_host,
                                                                            orchestrator.event_port))

        self.consume_channel = self.connection.channel()
        self._is_interrupted = False
        self.termination_result = self.consume_channel.queue_declare(queue='', exclusive=True)
        self.termination_queue_name = self.termination_result.method.queue
        self.consume_channel.queue_bind(exchange='brise_termination_sender', queue=self.termination_queue_name)

        self.consume_channel.basic_consume(queue='measurement_results_queue', auto_ack=True,
                                           on_message_callback=self.orchestrator.measure_configurations)
        self.consume_channel.basic_consume(queue='measure_new_configuration_queue', auto_ack=True,
                                           on_message_callback=self.orchestrator.measure_configurations)
        self.consume_channel.basic_consume(queue=self.termination_queue_name, auto_ack=True,
                                           on_message_callback=self.stop)

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

    def stop(self, ch = None, method = None, properties = None, body = None):
        self._is_interrupted = True
