import math

from stop_condition.stop_condition import StopCondition


class AdaptiveType(StopCondition):

    def __init__(self, stop_condition_parameters: dict, experiment_description: dict, experiment_id: str):
        super().__init__(stop_condition_parameters, experiment_description, experiment_id)
        search_space_size = \
            self.database.get_last_record_by_experiment_id("Search_space", self.experiment_id)["Search_space_size"]
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
        numb_of_measured_configurations = \
            self.database.get_last_record_by_experiment_id("Experiment_state", self.experiment_id)["Number_of_measured_configs"]
        if numb_of_measured_configurations >= self.max_configs:
            self.decision = True
        self.logger.debug(f"Number of measured configurations - {numb_of_measured_configurations}. Maximum - {self.max_configs}")
