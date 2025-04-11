from abc import ABC, abstractmethod

from core_entities.configuration import Configuration
from core_entities.experiment import Experiment


class DefaultConfigurationHandler(ABC):

    def __init__(self, default_configuration_handler_description: dict, experiment: Experiment):
        self.default_configuration_handler_description = default_configuration_handler_description
        self.experiment = experiment
        self.search_space_description = self.experiment.description["Context"]["SearchSpace"]

    @abstractmethod
    def get_default_configuration(self) -> Configuration:
        pass
