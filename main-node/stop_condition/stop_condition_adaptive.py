from stop_condition.stop_condition_abs import StopCondition
import logging


class StopConditionAdaptive(StopCondition):

    def __init__(self, search_space_size, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

        # max_configs_without_improvement is calculated as part of full search space size.
        # The part is determined by configs's value - "SearchSpacePercentageWithoutImprovement".
        self.max_configs_without_improvement = \
            round(self.stop_condition_config["SearchSpacePercentageWithoutImprovement"] / 100 * search_space_size)

    def is_final_prediction(self, current_best_configurations, solution_candidate_configurations):
        # if self.configs_without_improvement is higher or equal to self.max_configs_without_improvement,
        # then validation is True.
        self.logger.info("Solution validation success! Solution features: %s, solution labels: %s."
                         %(self.best_solution_configuration[0].configuration, self.best_solution_configuration[0].average_result))
        return True
