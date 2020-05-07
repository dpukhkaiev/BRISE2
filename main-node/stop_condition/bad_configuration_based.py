from stop_condition.stop_condition import StopCondition


class BadConfigurationBasedType(StopCondition):

    def __init__(self, stop_condition_parameters: dict, experiment_description: dict, experiment_id: str):
        super().__init__(stop_condition_parameters, experiment_description, experiment_id)
        self.threshold = stop_condition_parameters["Parameters"]["MaxBadConfigurations"]
        self.start_threads()

    def is_finish(self):
        bad_configurations_number = self.database.get_last_record_by_experiment_id("Experiment_state", self.experiment_id)["Number_of_bad_configs"]
        if bad_configurations_number >= self.threshold:
            self.decision = True
        self.logger.debug(f"Currently {bad_configurations_number} bad Configurations in Experiment.")
