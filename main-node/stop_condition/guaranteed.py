from stop_condition.stop_condition import StopCondition
from core_entities.experiment import Experiment


class GuaranteedType(StopCondition):

    def __init__(self, experiment: Experiment, stop_condition_parameters: dict):
        super().__init__(experiment, stop_condition_parameters)
        self.start_threads()

    def is_finish(self):
        current_best_configuration = self.experiment.get_current_solution()
        default_configuration = self.experiment.search_space.get_default_configuration()
        if current_best_configuration != default_configuration:
            self.decision = True
        self.logger.debug(f"Default Configuration - {default_configuration}. "
                          f"Current best Configuration - {current_best_configuration}.")
