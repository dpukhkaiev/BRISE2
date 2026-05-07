class RepeaterOrchestrationMock:

    def __init__(self, experiment_id: str, experiment=None):
        self.logger = logging.getLogger(__name__)
        self.experiment_id = experiment_id

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

        self.logger.info("Outliers detection module is disabled")

        self._type = self.get_repeater(True)



    def get_repeater(self, is_default_configuration: bool = False):
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

        return repeater_class(self.experiment_description, self.experiment_id, self.experiment)


    # probbaly doesnt need new impl
    def evaluation_by_type(self, current_configuration: Configuration):
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
        result = json.loads(body)

        configuration = Configuration.from_json(result["configuration"])

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

        return configuration, needed_tasks_count
