from abc import ABC, abstractmethod

from core_entities.configuration import Configuration
from core_entities.experiment import Experiment


class DefaultConfigurationHandler(ABC):

    def __init__(self, default_configuration_handler_description: dict, experiment: Experiment):
        self.default_configuration_handler_description = default_configuration_handler_description
        self.experiment = experiment
        self.search_space_description = self.experiment.description["Context"]["SearchSpace"]

    def get_default_configuration(self) -> Configuration:
        default_configuration = self._build_default_configuration()
        if default_configuration.prediction_info is None:
            # ensure uniformity with sampled configurations in DB
            default_configuration.prediction_info = {
                str(i): {"Model": [], "time_to_build": 0} for i in range(len(self.experiment.search_space.regions))
            }
        return default_configuration

    @abstractmethod
    def _build_default_configuration(self) -> Configuration:
        pass
