from stop_condition.stop_condition import StopCondition
from core_entities.experiment import Experiment


class QuantityBasedType(StopCondition):

    def __init__(self, experiment: Experiment, stop_condition_parameters: dict):
        super().__init__(experiment, stop_condition_parameters)
        self.max_configs = stop_condition_parameters["Parameters"]["MaxConfigs"]
        self.start_threads()

    def is_finish(self):
        n_measured_configs = self.experiment.get_number_of_measured_configurations()
        if n_measured_configs >= self.max_configs:
            self.decision = True
        self.logger.debug(f"Number of measured configurations - {n_measured_configs}. Maximum - {self.max_configs}")
