from stop_condition.stop_condition import StopCondition
from core_entities.experiment import Experiment


class QuantityBasedType(StopCondition):

    def __init__(self, experiment: Experiment, stop_condition_parameters: dict):
        super().__init__(experiment, stop_condition_parameters)
        self.max_configs = stop_condition_parameters["Parameters"]["MaxConfigs"]
        self.start_threads()

    def is_finish(self):
        number_of_measured_configurations = self.experiment.get_number_of_measured_configurations()
        if number_of_measured_configurations >= self.max_configs:
            self.logger.info("Quantity-based Stop Condition suggested to stop BRISE. "
                             "Number of measured configurations - %s. "
                             "Max configurations - %s" %(number_of_measured_configurations, self.max_configs))
            self.decision = True
            self.update_expression(self.stop_condition_type, self.decision)
