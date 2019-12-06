from stop_condition.stop_condition_decorator_posterior import StopConditionDecoratorPosterior

class DefaultType(StopConditionDecoratorPosterior):

    def __init__(self, stop_condition, stop_condition_parameters):
        super().__init__(stop_condition, __name__)
        self.max_configs = stop_condition_parameters["MaxConfigs"]

    def is_finish(self):
        number_of_measured_configurations = self.get_experiment().get_number_of_measured_configurations()
        if number_of_measured_configurations >= self.max_configs:
            self.logger.info("Default Stop Condition suggested to stop BRISE. "
                             "Number of measured configurations - %s. "
                             "Max configurations - %s" %(number_of_measured_configurations, self.max_configs))
            return True
        else:
            self.logger.info("Default Stop Condition suggested to continue running BRISE. "
                             "Number of measured configurations - %s. "
                             "Max configurations - %s" %(number_of_measured_configurations, self.max_configs))
            return False
