from stop_condition.stop_condition import StopCondition


class GuaranteedType(StopCondition):

    def __init__(self, stop_condition_parameters: dict, experiment_description: dict, experiment_id: str):
        super().__init__(stop_condition_parameters, experiment_description, experiment_id)
        self.start_threads()

    def is_finish(self):
        current_best_configuration = self.database.get_last_record_by_experiment_id("Experiment_state", self.experiment_id)["Current_solution"]
        default_configuration = self.database.get_last_record_by_experiment_id("Search_space", self.experiment_id)["Default_configuration"]
        if current_best_configuration != default_configuration:
            self.decision = True
        self.logger.debug(f"Default Configuration - {default_configuration}. "
                        f"Current best Configuration - {current_best_configuration}.")
