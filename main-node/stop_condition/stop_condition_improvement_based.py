from stop_condition.stop_condition_abs import StopCondition
import logging


class StopConditionImprovementBased(StopCondition):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.max_configs_without_improvement = self.stop_condition_config["MaxConfigsWithoutImprovement"]

    def is_final_prediction(self, current_best_configurations, solution_candidate_configurations):
        # If best_solution_labels value is better, than default value, validation is True.
        if (self.is_minimization_experiment is True and self.best_solution_configuration < current_best_configurations) or \
                (self.is_minimization_experiment is False and self.best_solution_configuration > current_best_configurations):
            self.logger.info("Solution validation success! Solution features: %s, solution labels: %s."
                             %(self.best_solution_configuration[0].configuration, self.best_solution_configuration[0].average_result))
            return True
        # If best_solution_labels value is worse, than default value, add this point to data set and rebuild model.
        else:
            self.logger.info("Found best solution value %s is worse, then default value %s."
                             % (solution_candidate_configurations[0].average_result, current_best_configurations[0].average_result))
            return False
