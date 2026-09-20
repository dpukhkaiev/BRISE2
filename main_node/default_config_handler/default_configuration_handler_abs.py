from abc import ABC, abstractmethod
from typing import List

import pandas as pd

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
            # ensure uniformity with sampled/predicted configurations in DB; only include the regions
            # activated by this configuration's parameter values
            traversed_region_indices = self._get_traversed_region_indices(default_configuration)
            default_configuration.prediction_info = {
                str(i): {"Model": [], "time_to_build": 0} for i in traversed_region_indices
            }
        return default_configuration

    def _get_traversed_region_indices(self, configuration: Configuration) -> List[int]:
        search_space = self.experiment.search_space
        parameters = pd.DataFrame([configuration.parameters])
        activated_regions = search_space.get_regions_on_current_level()
        traversed_region_indices = []
        while len(activated_regions) > 0:
            for region in activated_regions:
                traversed_region_indices.append(search_space.regions.index(region))
            search_space.next_level()
            activated_regions = search_space.activate_regions(parameters)
        search_space.reset_level()
        return traversed_region_indices

    @abstractmethod
    def _build_default_configuration(self) -> Configuration:
        pass
