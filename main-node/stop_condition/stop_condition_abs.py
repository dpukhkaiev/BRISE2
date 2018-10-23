from abc import ABC, abstractmethod


class StopCondition(ABC):

    # def __init__(self, io, task_config, repeater, default_value, predicted_features):
    #     self.io_event = io
    #     self.task_config = task_config
    #     self.repeater = repeater
    #     self.default_value = default_value
    #     self.predicted_features = predicted_features

    @abstractmethod
    def validate_solution(self, io, task_config, repeater, default_value, predicted_features): pass
