from stop_condition.stop_condition_abs import StopCondition
from tools.features_tools import split_features_and_labels
import logging


class StopConditionDefault(StopCondition):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def validate_solution(self, model_config, solution_candidate, current_best_solution):
        """
        Returns prediction_is_final=False if current_best_solution is better than solution_candidate_label,
                prediction_is_final=True if solution_candidate_label is better than current_best_solution
        :return: solution_labels, solution_feature, prediction_is_final
        """

        self.logger.info("Verifying solution that model gave..")

        solution_candidate_features, solution_candidate_labels = \
            split_features_and_labels(solution_candidate, model_config["FeaturesLabelsStructure"])

        # If our measured point is better than default best value - add this point to data set and rebuild model.
        # validate false
        if self.minimization_task_bool is True and solution_candidate_labels[0][0] > current_best_solution[0][0]:
            self.logger.info("Predicted value larger than default: %s > %s" % (solution_candidate_labels[0][0],
                                                                               current_best_solution[0][0]))
            prediction_is_final = False
        elif self.minimization_task_bool is False and solution_candidate_labels[0][0] < current_best_solution[0][0]:
            self.logger.info("Predicted value lower than default: %s < %s" % (solution_candidate_labels[0][0],
                                                                              current_best_solution[0][0]))
            prediction_is_final = False
        else:
            self.logger.info("Solution validation success!")
            prediction_is_final = True
        return solution_candidate_labels[0], solution_candidate_features[0], prediction_is_final
