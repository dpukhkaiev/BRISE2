from abc import ABC, abstractmethod
from core_entities.experiment import Experiment
from core_entities.configuration import Configuration


class AbstractDefaultConfigurationHandler(ABC):

    def __init__(self, experiment: Experiment):
        self.experiment = experiment

    @abstractmethod
    def get_default_config(self) -> Configuration: pass
