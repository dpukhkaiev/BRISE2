from stop_condition.stop_condition_abs import StopCondition
from tools.features_tools import split_features_and_labels
import logging


class StopConditionDefault(StopCondition):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.max_configs_without_improvement = 0
        self.best_solution_labels = [[]]
        self.best_solution_features = [[]]

    def validate_solution(self, solution_candidate_labels, solution_candidate_features, current_best_solution):
        """
        Returns prediction_is_final=True if solution_candidate_label is better than current_best_solution and
                max_configs_without_improvement < 0, otherwise prediction_is_final=False
        :return: labels,
                     shape - list of lists, e.g. ``[[253.132]]``
                 feature,
                     shape - list of lists, e.g. ``[[2000.0, 32]]``
                 prediction_is_final

        """
        prediction_is_final = False

        if self.best_solution_labels == [[]]:
            self.best_solution_labels = current_best_solution
            self.max_configs_without_improvement = self.stop_condition_config["MaxConfigsWithoutImprovement"]

        # If the measured point is worse than previous best value - add this point to data set and rebuild model.
        # validation is false
        if (self.is_minimization_experiment is True and solution_candidate_labels[0][0] > self.best_solution_labels[0][0]) \
                or (self.is_minimization_experiment is False and solution_candidate_labels[0][0] < self.best_solution_labels[0][0]):
            self.max_configs_without_improvement -= 1
            self.logger.info("Predicted value is worse than previous value: %s, %s. Max Configs Without Improvement = %s" %
                             (solution_candidate_labels, self.best_solution_labels, self.max_configs_without_improvement))

        # If the measured point is better than previous best value - add this point to data set and rebuild model.
        # validation is false
        elif (self.is_minimization_experiment is True and solution_candidate_labels[0][0] < self.best_solution_labels[0][0]) \
                or (self.is_minimization_experiment is False and solution_candidate_labels[0][0] > self.best_solution_labels[0][0]):
            self.best_solution_labels = solution_candidate_labels
            self.best_solution_features = solution_candidate_features
            self.max_configs_without_improvement = self.stop_condition_config["MaxConfigsWithoutImprovement"]
            self.logger.info("New solution is found! Predicted value is better than previous value: %s, %s. "
                             "Max Configs Without Improvement = %s" % (solution_candidate_labels, self.best_solution_labels,
                                                                       self.max_configs_without_improvement))

        # if self.max_configs_without_improvement is lower than 0 and self.best_solution_features is not 0 validation is True.
        # self.best_solution_features is not 0, which means that there is a label, that better then current_best_solution.
        if self.max_configs_without_improvement < 0 and self.best_solution_features != [[]]:
            self.logger.info("Solution validation success!")
            prediction_is_final = True
            return self.best_solution_labels, self.best_solution_features, prediction_is_final

        return solution_candidate_labels, solution_candidate_features, prediction_is_final
