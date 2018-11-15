from abc import ABC, abstractmethod
from tools.is_better_point import is_better_point


class StopCondition(ABC):

    def __init__(self, is_minimization_experiment, stop_condition_config):
        self.is_minimization_experiment = is_minimization_experiment
        self.stop_condition_config = stop_condition_config
        self.configs_without_improvement = 0
        self.best_solution_labels = [[]]
        self.best_solution_features = [[]]
        self.prediction_is_final = False
        self.max_configs_without_improvement = 0

    # Template method
    def validate_solution(self, solution_candidate_labels, solution_candidate_features, current_best_labels,
                          current_best_features):
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
        self.initial_assignment(current_best_features, current_best_labels)
        if self.configs_without_improvement < self.max_configs_without_improvement:
            self.compare_configurations(solution_candidate_labels, solution_candidate_features)
        if self.configs_without_improvement >= self.max_configs_without_improvement:
            self.prediction_is_final = self.is_final_prediction(current_best_labels, solution_candidate_labels)

        if self.prediction_is_final is True:
            return self.best_solution_labels, self.best_solution_features, self.prediction_is_final
        else:
            return solution_candidate_labels, solution_candidate_features, self.prediction_is_final

    def initial_assignment(self, current_best_features, current_best_labels):
        if self.best_solution_labels == [[]] or self.best_solution_features == [[]]:
            self.best_solution_labels = current_best_labels
            self.best_solution_features = current_best_features

    # @abstractmethod
    # def continue_comparison(self): pass

    def compare_configurations(self, solution_candidate_labels, solution_candidate_features):
        # If the measured point is better than previous best value - add this point to data set and rebuild model.
        # Assign self.configs_without_improvement to its configuration value.
        if is_better_point(is_minimization_experiment=self.is_minimization_experiment,
                           solution_candidate_label=solution_candidate_labels[0][0],
                           best_solution_label=self.best_solution_labels[0][0]):
            self.configs_without_improvement = 0
            self.logger.info("New solution is found! Predicted value %s is better than previous value %s. "
                             "Configs Without Improvement = %s" % (solution_candidate_labels,
                                                                       self.best_solution_labels,
                                                                       self.configs_without_improvement))
            self.best_solution_labels = solution_candidate_labels
            self.best_solution_features = solution_candidate_features

        # If the measured point is worse than previous best value - add this point to data set and rebuild model.
        # Decrease self.configs_without_improvement by 1
        else:
            self.configs_without_improvement += 1
            self.logger.info("Predicted value %s is worse than previous value %s. Configs Without Improvement = %s"
                             % (solution_candidate_labels, self.best_solution_labels, self.configs_without_improvement))

    @abstractmethod
    def is_final_prediction(self, current_best_labels, solution_candidate_labels): pass
