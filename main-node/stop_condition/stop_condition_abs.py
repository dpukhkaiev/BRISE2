from abc import ABC, abstractmethod


class StopCondition(ABC):

    def __init__(self, minimization_task_bool):
        self.minimization_task_bool = minimization_task_bool

    @abstractmethod
    def validate_solution(self, io, model_config, solution_candidate, current_best_solution):
        """
        :param io: Web API object
        :param model_config: dictionary
               Dictionary of Model configuration, which is stored in Resources/task.json
        :param solution_candidate: list of lists with features and labels.
               solution_candidate_labels to be validated as a new solution.
               shape - list of lists, e.g. ``[[1900.0, 32, 435.51]]``
        :param current_best_solution: list of lists with one current best value
               current_best_solution is always a default_value for the "StopConditionDefault" case.
               shape - list of lists with one value, e.g. ``[[326.273]]``
        """
        pass
