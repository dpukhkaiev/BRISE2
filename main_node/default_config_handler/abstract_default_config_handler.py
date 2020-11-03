from abc import ABC, abstractmethod

from core_entities.configuration import Configuration
from core_entities.experiment import Experiment


class AbstractDefaultConfigurationHandler(ABC):

    def __init__(self, experiment: Experiment):
        self.experiment = experiment

    @abstractmethod
    def get_default_config(self) -> Configuration:
        pass

    def get_new_default_config(self):
        return self.get_default_config()
