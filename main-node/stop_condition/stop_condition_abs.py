from abc import ABC, abstractmethod


class StopCondition(ABC):

    def __init__(self, minimization_task_bool):
        self.minimization_task_bool = minimization_task_bool

    @abstractmethod
    def validate_solution(self, io, task_config, predicted_features): pass
