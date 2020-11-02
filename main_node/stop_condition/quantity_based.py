from stop_condition.stop_condition import StopCondition


class QuantityBasedType(StopCondition):

    def __init__(self, stop_condition_parameters: dict, experiment_description: dict, experiment_id: str):
        super().__init__(stop_condition_parameters, experiment_description, experiment_id)
        self.max_configs = stop_condition_parameters["Parameters"]["MaxConfigs"]
        self.start_threads()

    def is_finish(self):
        numb_of_measured_configurations = \
            self.database.get_last_record_by_experiment_id("Experiment_state", self.experiment_id)["Number_of_measured_configs"]
        if numb_of_measured_configurations >= self.max_configs:
            self.decision = True
        self.logger.debug(f"Number of measured configurations - {numb_of_measured_configurations}. Maximum - {self.max_configs}")
