from stop_condition.stop_condition_abs import StopCondition
import logging


class StopConditionDefault(StopCondition):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.max_configs_without_improvement = self.stop_condition_config["MaxConfigsWithoutImprovement"]


    # def continue_comparison(self):
    #     if self.configs_without_improvement < self.stop_condition_config["MaxConfigsWithoutImprovement"]:
    #         return True
    #     else:
    #         return False

    def is_final_prediction(self, current_best_labels, solution_candidate_labels):
        # if self.configs_without_improvement is higher or equal to
        # self.stop_condition_config["MaxConfigsWithoutImprovement"], then validation is True.
        self.logger.info("Solution validation success! Solution features: %s, solution labels: %s."
                         %(self.best_solution_features,self.best_solution_labels))
        return True
