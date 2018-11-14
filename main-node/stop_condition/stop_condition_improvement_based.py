from stop_condition.stop_condition_abs import StopCondition
import logging
from tools.is_better_point import is_better_point


class StopConditionImprovementBased(StopCondition):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def find_solution(self):
        if self.configs_without_improvement < self.stop_condition_config["MaxConfigsWithoutImprovement"]:
            return True
        else:
            return False

    def solution_validation(self, current_best_labels, solution_candidate_labels):
        # If best_solution_labels value is better, than default value, validation is True.
        if is_better_point(is_minimization_experiment=self.is_minimization_experiment,
                           solution_candidate_label=self.best_solution_labels[0][0],
                           best_solution_label=current_best_labels[0][0]):
            self.logger.info("Solution validation success! Solution features: %s, solution labels: %s."
                             %(self.best_solution_features,self.best_solution_labels))
            self.prediction_is_final = True
        # If best_solution_labels value is worse, than default value, add this point to data set and rebuild model.
        else:
            self.logger.info("Found best solution value %s is worse, then default value %s."
                             % (solution_candidate_labels, current_best_labels))
