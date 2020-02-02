from abc import ABC, abstractmethod
from typing import List

from core_entities.configuration import Configuration


class Model(ABC):
    @abstractmethod
    def build_model(self): pass

    @abstractmethod
    def validate_model(self): pass

    @abstractmethod
    def predict_next_configurations(self, number):
        # TODO: Make it `template method` or 'strategy'.
        return Configuration
