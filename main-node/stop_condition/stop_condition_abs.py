from abc import ABC, abstractmethod


class StopCondition(ABC):

    def __init__(self, minimization_task_bool, stop_condition_config):
        self.minimization_task_bool = minimization_task_bool
        self.stop_condition_config = stop_condition_config

    @abstractmethod
    def validate_solution(self, solution_candidate_labels, solution_candidate_features, current_best_solution):
        """
        :param solution_candidate_labels: list of lists with labels of solution candidate. To be validated as a new
                                          solution.
               shape - list of lists, e.g. ``[[435.51]]``
        :param solution_candidate_features: list of lists with features of solution candidate.
               shape - list of lists, e.g. ``[[1900.0, 32]]``
        :param current_best_solution: list of lists with one current best value.
               current_best_solution is always a default_value for the "StopConditionDefault" case.
               shape - list of lists with one value, e.g. ``[[326.273]]``
        """
        pass
