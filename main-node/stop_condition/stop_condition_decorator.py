import logging

class StopConditionDecorator:
    
    def __init__(self, stop_condition):
        self.stop_condition = stop_condition
        self.logger = logging.getLogger(__name__)

    def validate_conditions(self):
        if self.get_experiment().get_number_of_measured_configurations() == self.get_experiment().get_search_space_size():
            self.logger.info("StopConditionDecorator: BRISE has measured the entire Search Space. Reporting the best found Configuration.")
            return True
        return self.stop_condition.validate_conditions() and self.is_finish()

    def update_number_of_configurations_in_iteration(self, number_of_configurations_in_iteration):
        self.stop_condition.update_number_of_configurations_in_iteration(number_of_configurations_in_iteration)

    def get_experiment(self):
        return self.stop_condition.get_experiment()

    def _compare_best_configurations(self, candidate_configurations):
        return self.stop_condition._compare_best_configurations(candidate_configurations)

    def is_finish(self): pass

    def get_best_configurations(self):
        return self.stop_condition.get_best_configurations()