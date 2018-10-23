from abc import ABC, abstractmethod


class StopCondition(ABC):

    @abstractmethod
    def validate_solution(self, io, task_config, repeater, default_value, predicted_features): pass
