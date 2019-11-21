from stop_condition.stop_condition_decorator_posterior import StopConditionDecoratorPosterior

class AdaptiveType(StopConditionDecoratorPosterior):

    def __init__(self, stop_condition, stop_condition_parameters):
        super().__init__(stop_condition, __name__)
        try:
            self.max_configs = \
                round(stop_condition_parameters["SearchSpacePercentage"] / 100 * float(self.get_experiment().search_space.get_search_space_size()))
        except Exception:
            self.logger.warning("Unable to create an instance of Adaptive stop-condition.")
    
    def is_finish(self):
        number_of_measured_configurations = self.get_experiment().get_number_of_measured_configurations()
        if number_of_measured_configurations >= self.max_configs:
            self.logger.info("Adaptive Stop Condition suggested to stop BRISE. "
                             "Number of measured configurations - %s. "
                             "Max configurations - %s" %(number_of_measured_configurations, self.max_configs))
            return True
        else:
            self.logger.info("Adaptive Stop Condition suggested to continue running BRISE. "
                             "Number of measured configurations - %s. "
                             "Max configurations - %s" %(number_of_measured_configurations, self.max_configs))
            return False
