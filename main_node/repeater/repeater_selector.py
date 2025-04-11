import json
import logging
import os

from core_entities.configuration import Configuration
from repeater.results_check.outliers_detection.outliers_detector_selector import (
    get_outlier_detectors
)
from repeater.results_check.task_errors_check import error_check
from tools.front_API import API
from tools.mongo_dao import MongoDB
from tools.rabbitmq_common_tools import RabbitMQConnection, publish
from tools.reflective_class_import import reflective_class_import

logging.getLogger("pika").propagate = False


class RepeaterOrchestration:
    """
    This class runs repeater creation process, task preprocessing (errors, outliers check)
    and configuration status management.
    """

    def __init__(self, experiment_id: str, experiment=None):
        """
        :param experiment_id: ID of experiment, required to get experiment description from DB
        :param experiment: Experiment class instance, (!)used only in tests
        """
        self.logger = logging.getLogger(__name__)
        self.experiment_id = experiment_id
        if os.environ.get('TEST_MODE') != 'UNIT_TEST':
            self.database = MongoDB(os.getenv("BRISE_DATABASE_HOST"),
                                    os.getenv("BRISE_DATABASE_PORT"),
                                    os.getenv("BRISE_DATABASE_NAME"),
                                    os.getenv("BRISE_DATABASE_USER"),
                                    os.getenv("BRISE_DATABASE_PASS"))

            self.experiment_description = None
            while self.experiment_description is None:
                self.experiment_description = self.database.get_last_record_by_experiment_id("Experiment_description", experiment_id)
        else:
            self.database = MongoDB("test", 0, "test", "user", "pass")
            self.experiment = experiment
            self.experiment_description = experiment.description
        self.performed_measurements = 0

        keys = list(self.experiment_description["RepetitionManager"]["Instance"].keys())
        assert len(keys) == 1
        feature_name = keys[0]
        self.repeater_parameters = {**self.experiment_description["RepetitionManager"]["Instance"][feature_name], **self.experiment_description["RepetitionManager"]}

        objectives = [self.experiment_description["Context"]["TaskConfiguration"]["Objectives"][key]["Name"]
                 for key in self.experiment_description["Context"]["TaskConfiguration"]["Objectives"].keys()]
        self._objectives = objectives
        data_types = [self.experiment_description["Context"]["TaskConfiguration"]["Objectives"][key]["DataType"]
                      for key in self.experiment_description["Context"]["TaskConfiguration"]["Objectives"].keys()]

        self._objectives_data_types = data_types
        minimal_values = [self.experiment_description["Context"]["TaskConfiguration"]["Objectives"][key]["MinExpectedValue"]
                      for key in self.experiment_description["Context"]["TaskConfiguration"]["Objectives"].keys()]
        maximal_values = [self.experiment_description["Context"]["TaskConfiguration"]["Objectives"][key]["MaxExpectedValue"]
                      for key in self.experiment_description["Context"]["TaskConfiguration"]["Objectives"].keys()]
        expected_value_ranges = [(min, max) for min in minimal_values for max in maximal_values]
        self._expected_values_range = expected_value_ranges

        # TODO Outliers are disabled
        # if self.metric_description["OutliersDetection"]["isEnabled"]:
        #     self.outlier_detectors = get_outlier_detectors(self.metric_description["OutliersDetection"])
        # else:
        self.logger.info("Outliers detection module is disabled")

        self._type = self.get_repeater(True)
        if os.environ.get('TEST_MODE') != 'UNIT_TEST':
            self.connection_thread = self._EventServiceConnection(self)
            self.channel = self.connection_thread.channel
            self.connection_thread.start()

    def get_repeater(self, is_default_configuration: bool = False):
        """
        This method selects concrete instance of the Repeater class, for default configuration Quantity-based repeater
        should be used
        :param is_default_configuration: is Repeater called to measure default configuration? default=False
        :return instance of a concrete Repeater
        """
        logger = logging.getLogger(__name__)
        parameters = self.experiment_description["RepetitionManager"]

        keys = list(self.experiment_description["RepetitionManager"]["Instance"].keys())
        assert len(keys) == 1
        feature_name = keys[0]

        if not is_default_configuration:
            repeater_class = reflective_class_import(class_name=parameters["Instance"][feature_name]["Type"], folder_path="repeater")
        else:
            repeater_class = reflective_class_import(class_name="quantity_based", folder_path="repeater")

        msg = parameters["Instance"][feature_name]["Type"]
        logger.debug(f"Assigned {msg} Repetition Management strategy.")
        if os.environ.get('TEST_MODE') != 'UNIT_TEST':
            return repeater_class(self.experiment_description, self.experiment_id)
        else:
            return repeater_class(self.experiment_description, self.experiment_id, self.experiment)

    def evaluation_by_type(self, current_configuration: Configuration):
        """
        Forwards a call to specific Repeater Type to evaluate if Configuration was measured precisely.
        :param current_configuration: instance of Configuration class.
        :returns: int Number of measurements of Configuration which need to be performed, EvaluationStatus
        """

        if self._type is None:
            raise TypeError("Repeater evaluation Type was not selected!")
        else:
            if not current_configuration.status['evaluated'] or current_configuration.results:
                number_of_measurements = self._type.evaluate(current_configuration=current_configuration)
                current_configuration.status['evaluated'] = True
                if number_of_measurements == 0:
                    current_configuration.status['measured'] = True
                return number_of_measurements
            else:
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
        if configuration.status['evaluated'] and os.environ.get('TEST_MODE') != 'UNIT_TEST':
            tasks_to_send = result["tasks_to_send"]
            tasks_results = result["tasks_results"]
            for index, objective in enumerate(self._objectives):
                tasks_results = error_check(tasks_results,
                                            objective,
                                            self._expected_values_range[index],
                                            self._objectives_data_types[index])
            # if self.metric_description["OutliersDetection"]["isEnabled"]: # TODO enable outliers
            #     tasks_results = self.outlier_detectors.find_outliers_for_taskset(tasks_results,
            #                                                                      self._objectives,
            #                                                                      [configuration],
            #                                                                      tasks_to_send)

            # Sending data to API and adding Tasks to Configuration
            for parameters, task in zip(tasks_to_send, tasks_results):
                if configuration.parameters == parameters:
                    if configuration.is_valid_task(task):
                        configuration.add_task(task)
                        self.database.write_one_record("Task", configuration.get_task_record(task))

                API().send('new', 'task', configurations=[parameters], results=[task])

        # Evaluating configuration
        if configuration.number_of_failed_tasks <= self.repeater_parameters['MaxFailedTasksPerConfiguration']:
            needed_tasks_count = self.evaluation_by_type(configuration)
        else:
            needed_tasks_count = 0
            configuration.status['enabled'] = False
            configuration.status['measured'] = True
            if len(configuration.get_tasks()) == 0:
                publish(exchange="experiment_api_exchange",
                        routing_key=self.experiment_id,
                        body="increment_bad_configuration_number")
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
                    self.database.update_record(
                        "Experiment_state",
                        {"Exp_unique_ID": self.experiment_id},
                        {
                            "Number_of_measured_tasks": self.performed_measurements
                        }
                    )

        if os.environ.get('TEST_MODE') == 'UNIT_TEST':
            return configuration, needed_tasks_count

        elif configuration.status['measured']:
            if configuration.type == Configuration.Type.DEFAULT:
                self._type = self.get_repeater()
                publish(exchange='default_configuration_results_exchange',
                        routing_key=self.experiment_id,
                        body=configuration.to_json())
            elif configuration.type == Configuration.Type.PREDICTED or \
                    configuration.type == Configuration.Type.FROM_SELECTOR or \
                    configuration.type == Configuration.Type.TRANSFERRED:
                publish(exchange='configurations_results_exchange',
                        routing_key=self.experiment_id,
                        body=configuration.to_json())
        elif configuration.status['evaluated']:
            body = json.dumps({"configuration": configuration.to_json(), "tasks": tasks_to_send})
            publish(exchange='process_tasks_exchange',
                    routing_key=self.experiment_id,
                    body=body)

    class _EventServiceConnection(RabbitMQConnection):
        """
        This class runs in a separate thread and handles measurement result from WSClient,
        connected to the `measurement_results_exchange` as consumer and recheck measurement by repeater.measure_configurations
        """
        def __init__(self, orchestrator):
            """
            :param orchestrator: an instance of Repeater Orchestrator object
            """
            self.orchestrator: RepeaterOrchestration = orchestrator
            self.experiment_id = self.orchestrator.experiment_id
            super().__init__(orchestrator)

        def bind_and_consume(self):
            self.termination_result = self.channel.queue_declare(queue='', exclusive=True)
            self.termination_queue_name = self.termination_result.method.queue
            self.channel.queue_bind(exchange='experiment_termination_exchange',
                                    queue=self.termination_queue_name,
                                    routing_key=self.experiment_id)
            self.channel.basic_consume(queue='measurement_results_exchange' + self.experiment_id, auto_ack=True,
                                       on_message_callback=self.orchestrator.measure_configurations)
            self.channel.basic_consume(queue='measure_new_configuration_exchange' + self.experiment_id, auto_ack=True,
                                       on_message_callback=self.orchestrator.measure_configurations)
            self.channel.basic_consume(queue=self.termination_queue_name, auto_ack=True,
                                       on_message_callback=self.stop)
