import logging

from stop_condition.stop_condition_decorator import StopConditionDecorator

class GuaranteedType(StopConditionDecorator):
    def __init__(self, stop_condition, stop_condition_parameters):
        super().__init__(stop_condition)
        self.logger = logging.getLogger(__name__)

    def is_finish(self):
        experiment = self.get_experiment()
        current_best_configuration = experiment.get_current_solution()
        if current_best_configuration.is_better_configuration(experiment.is_minimization(), experiment.default_configuration):
            self.logger.info("Guaranteed Stop Condition suggested to stop BRISE. "
                             "Default Configuration - %s. "
                             "Current best Configuration - %s" %(experiment.default_configuration, current_best_configuration))
            return True
        else:
            self.logger.info("Guaranteed Stop Condition suggested to continue running BRISE. "
                             "Default Configuration - %s. "
                             "Current best Configuration - %s" %(experiment.default_configuration, current_best_configuration))
            return False