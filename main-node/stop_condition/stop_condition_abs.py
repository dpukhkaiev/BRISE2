from abc import ABC, abstractmethod


class StopCondition(ABC):

    def __init__(self, is_minimization_experiment, stop_condition_config):
        self.is_minimization_experiment = is_minimization_experiment
        self.stop_condition_config = stop_condition_config

    @abstractmethod
    def validate_solution(self, solution_candidate_labels, solution_candidate_features, current_best_labels,
                          current_best_features):
        """
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
        """
        pass
