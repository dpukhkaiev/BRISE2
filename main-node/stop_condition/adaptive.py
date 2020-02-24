from stop_condition.stop_condition import StopCondition
from core_entities.experiment import Experiment


class AdaptiveType(StopCondition):

    def __init__(self, experiment: Experiment, stop_condition_parameters: dict):
        super().__init__(experiment, stop_condition_parameters)
        try:
            self.max_configs = \
                round(stop_condition_parameters["Parameters"]["SearchSpacePercentage"] / 100 * float(self.experiment.search_space.get_search_space_size()))
            self.start_threads()
        except OverflowError:
            temp_msg = ("Error! Unable to create an instance of Adaptive stop-condition. Experiment will be stopped in a few seconds. "
                                "Please, check your experiment description")
            self.logger.error(temp_msg)
            self.stop_experiment_due_to_failed_sc_creation()

    def is_finish(self):
        number_of_measured_configurations = self.experiment.get_number_of_measured_configurations()
        if number_of_measured_configurations >= self.max_configs:
            self.logger.info("Adaptive Stop Condition suggested to stop BRISE. "
                            "Number of measured configurations - %s. "
                            "Max configurations - %s" %(number_of_measured_configurations, self.max_configs))
            self.decision = True
            self.update_expression(self.stop_condition_type, self.decision)
