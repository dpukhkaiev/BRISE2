import logging
from stop_condition.stop_condition_decorator import StopConditionDecorator
from stop_condition.stop_condition_posterior import StopConditionPosterior


class StopConditionDecoratorPosterior(StopConditionDecorator, StopConditionPosterior):

    def __init__(self, stop_condition, name):
        super().__init__(stop_condition)
        self.logger = logging.getLogger(name)

    def validate_conditions(self):
        if self.get_experiment().get_number_of_measured_configurations() == self.get_experiment().search_space.get_search_space_size():
            self.logger.info("StopConditionDecorator: BRISE has measured the entire Search Space. Reporting the best found Configuration.")
            return True
        return self.stop_condition.validate_conditions() and self.is_finish()

    def update_number_of_configurations_in_iteration(self, number_of_configurations_in_iteration):
        self.stop_condition.update_number_of_configurations_in_iteration(number_of_configurations_in_iteration)
    
    def _compare_best_configurations(self, candidate_configurations):
        return self.stop_condition._compare_best_configurations(candidate_configurations)

    def get_best_configurations(self):
        return self.stop_condition.get_best_configurations()
