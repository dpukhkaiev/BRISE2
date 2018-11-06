from stop_condition.stop_condition_abs import StopCondition
from tools.features_tools import split_features_and_labels
import logging


class StopConditionDefault(StopCondition):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.early_stop_criteria = 0
        self.best_solution_labels = 0
        self.best_solution_features = 0

    def validate_solution(self, early_stop_criteria, solution_candidate_labels, solution_candidate_features,
                          current_best_solution):
        """
        Returns prediction_is_final=True if solution_candidate_label is better than current_best_solution and
                early_stop_criteria < 0, otherwise prediction_is_final=False
        :return: labels,
                     shape - list of lists, e.g. ``[[253.132]]``
                 feature,
                     shape - list of lists, e.g. ``[[2000.0, 32]]``
                 prediction_is_final

        """
        prediction_is_final = False

        if self.best_solution_labels is 0:
            self.best_solution_labels = current_best_solution
            self.early_stop_criteria = early_stop_criteria

        # If our measured point is worse than previous best value - add this point to data set and rebuild model.
        # validation is false
        if (self.minimization_task_bool is True and solution_candidate_labels[0][0] > self.best_solution_labels[0][0]) \
                or (self.minimization_task_bool is False and solution_candidate_labels[0] < self.best_solution_labels[0]):
            self.early_stop_criteria -= 1
            self.logger.info("Predicted value is worse than previous value: %s, %s. Early stop criteria = %s" %
                             (solution_candidate_labels, self.best_solution_labels, self.early_stop_criteria))

        # If our measured point is better than previous best value - add this point to data set and rebuild model.
        # validation is false
        elif (self.minimization_task_bool is True and solution_candidate_labels[0][0] < self.best_solution_labels[0][0]) \
                or (self.minimization_task_bool is False and solution_candidate_labels[0][0] > self.best_solution_labels[0][0]):
            self.best_solution_labels = solution_candidate_labels
            self.best_solution_features = solution_candidate_features
            self.early_stop_criteria = early_stop_criteria
            self.logger.info("New solution is found! Predicted value is better than previous value: %s, %s. "
                             "Early stop criteria = %s" % (solution_candidate_labels, self.best_solution_labels,
                                                           self.early_stop_criteria))

        # if self.early_stop_criteria is lower than 0 and self.best_solution_features is not 0 validation is True.
        # self.best_solution_features is not 0, which means that there is a label, that better then current_best_solution.
        if self.early_stop_criteria < 0 and self.best_solution_features is not 0:
            self.logger.info("Solution validation success!")
            prediction_is_final = True
            return self.best_solution_labels, self.best_solution_features, prediction_is_final

        return solution_candidate_labels, solution_candidate_features, prediction_is_final
