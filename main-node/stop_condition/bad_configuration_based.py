from stop_condition.stop_condition_decorator_prior import StopConditionDecoratorPrior


class BadConfigurationBasedType(StopConditionDecoratorPrior):
    """
        Bad configuration based stop condition. 
        This SC will check number of configurations that didn't showed any correct results during measurements.
        If the number of these Configurations >= than MaxBadConfigurations, this SC will be triggered.
    """
    def __init__(self, stop_condition, stop_condition_parameters):
        super().__init__(stop_condition, __name__)
        self.threshold = stop_condition_parameters["MaxBadConfigurations"]


    def is_finish(self):
        bad_configurations_number = self.get_experiment().get_bad_configuration_number()
        if bad_configurations_number >= self.threshold:
            self.logger.info("Bad-configuration-based Stop Condition suggested to stop BRISE.")
            return True
        else:
            self.logger.info("Bad-configuration-based Stop Condition suggested to continue running BRISE.")
            return False

