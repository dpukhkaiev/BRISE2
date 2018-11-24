from abc import ABC, abstractmethod


class StopCondition(ABC):

    def __init__(self, is_minimization_experiment, stop_condition_config):
        self.is_minimization_experiment = is_minimization_experiment
        self.stop_condition_config = stop_condition_config
        self.configs_without_improvement = 0
        # self.best_solution_labels = [[]]
        # self.best_solution_features = [[]]
        self.prediction_is_final = False
        self.max_configs_without_improvement = 0

        self.best_solution_configuration = []

    # Template method
    def validate_solution(self, solution_candidate_configurations, current_best_configurations):
        """
        Returns prediction_is_final=True if configs_without_improvement >= "MaxConfigsWithoutImprovement",
                otherwise prediction_is_final=False
        :param solution_candidate_labels: list of lists with labels of solution candidate. To be validated as a new
                                          solution.
               shape - list of lists, e.g. ``[[435.51]]``
        :param solution_candidate_features: list of lists with features of solution candidate.
               shape - list of lists, e.g. ``[[1900.0, 32]]``
        :param current_best_labels: list of lists with labels of current best value.
               current_best_labels is always labels of default_value for the "StopConditionDefault" case.
               shape - list of lists with one value, e.g. ``[[326.273]]``
        :param current_best_features: list of lists with features of current best value.
               current_best_features is always features of default_value for the "StopConditionDefault" case.
               shape - list of lists, e.g. ``[[2900.0, 32]]``
        :return: labels,
                     shape - list of lists, e.g. ``[[253.132]]``
                 feature,
                     shape - list of lists, e.g. ``[[2000.0, 32]]``
                 prediction_is_final
        """
        if self.best_solution_configuration == [] or \
                self.best_solution_configuration[0].average_result[0] > current_best_configurations[0].average_result[0]:
            self.best_solution_configuration = current_best_configurations


        # if self.best_solution_labels == [[]] or self.best_solution_labels[0][0] > current_best_labels[0][0]:
        #     self.best_solution_labels = current_best_labels
        #     self.best_solution_features = current_best_features

        if self.configs_without_improvement < self.max_configs_without_improvement:
            self.compare_configurations(solution_candidate_configurations, current_best_configurations)

        if self.prediction_is_final is True:
            return self.best_solution_configuration, self.prediction_is_final
        else:
            return solution_candidate_configurations, self.prediction_is_final

    def compare_configurations(self, solution_candidate_configurations, current_best_configurations):
        # If the measured point is better than previous best value - add this point to data set and rebuild model.
        # Assign self.configs_without_improvement to its configuration value.
        if (self.is_minimization_experiment is True and solution_candidate_configurations < self.best_solution_configuration) or \
                (self.is_minimization_experiment is False and solution_candidate_configurations > self.best_solution_configuration):
            self.configs_without_improvement = 0
            self.logger.info("New solution is found! Predicted value %s is better than previous value %s. "
                             "Configs Without Improvement = %s" % (solution_candidate_configurations[0].average_result,
                                                                   self.best_solution_configuration[0].average_result,
                                                                   self.configs_without_improvement))
            self.best_solution_configuration = solution_candidate_configurations
            # self.best_solution_labels = solution_candidate_labels
            # self.best_solution_features = solution_candidate_features

        # If the measured point is worse than previous best value - add this point to data set and rebuild model.
        # Decrease self.configs_without_improvement by 1
        else:
            self.configs_without_improvement += 1
            self.logger.info("Predicted value %s is worse than previous value %s. Configs Without Improvement = %s"
                             % (solution_candidate_configurations[0].average_result,
                                self.best_solution_configuration[0].average_result,
                                self.configs_without_improvement))
            if self.configs_without_improvement >= self.max_configs_without_improvement:
                self.prediction_is_final = self.is_final_prediction(current_best_configurations,
                                                                    solution_candidate_configurations)

    @abstractmethod
    def is_final_prediction(self, current_best_configurations, solution_candidate_configurations): pass
