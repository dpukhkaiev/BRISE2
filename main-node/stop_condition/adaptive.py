import math

from stop_condition.stop_condition import StopCondition
from core_entities.experiment import Experiment


class AdaptiveType(StopCondition):

    def __init__(self, experiment: Experiment, stop_condition_parameters: dict):
        super().__init__(experiment, stop_condition_parameters)

        search_space_size = self.experiment.search_space.get_search_space_size()
        if math.isfinite(search_space_size):
            self.max_configs = \
                round(stop_condition_parameters["Parameters"]["SearchSpacePercentage"] / 100 * float(search_space_size))
            self.start_threads()
        else:
            temp_msg = ("Unable to use Adaptive Stop Condition when size of Search Space is infinite. "
                        "Experiment will be stopped in a few seconds. "
                        "Please, either remove Adaptive Stop Condition from Settings, or change your Search Space.")
            self.logger.error(temp_msg)
            self.stop_experiment_due_to_failed_sc_creation()

    def is_finish(self):
        n_measured_configs = self.experiment.get_number_of_measured_configurations()
        if n_measured_configs >= self.max_configs:
            self.decision = True
        self.logger.debug(f"Number of measured configurations - {n_measured_configs}. Maximum - {self.max_configs}")
