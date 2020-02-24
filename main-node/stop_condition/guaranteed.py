from stop_condition.stop_condition import StopCondition
from core_entities.experiment import Experiment


class GuaranteedType(StopCondition):

    def __init__(self, experiment: Experiment, stop_condition_parameters: dict):
        super().__init__(experiment, stop_condition_parameters)
        self.start_threads()

    def is_finish(self):
        current_best_configuration = self.experiment.get_current_solution()
        if self.experiment.get_current_solution() != self.experiment.search_space.get_default_configuration():
            self.logger.info("Guaranteed Stop Condition suggested to stop BRISE. "
                             "Default Configuration - %s. "
                             "Current best Configuration - %s" %(self.experiment.search_space.get_default_configuration(), current_best_configuration))
            self.decision = True
            self.update_expression(self.stop_condition_type, self.decision)
