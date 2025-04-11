import pandas as pd

from default_config_handler.default_configuration_handler_abs import DefaultConfigurationHandler
from core_entities.experiment import Experiment
from core_entities.configuration import Configuration


class BasicDefaultConfigurationHandler(DefaultConfigurationHandler):
    """
    Extracts a user-defined default configuration from the search space description
    """
    def __init__(self, default_configuration_handler_description: dict, experiment: Experiment):
        super().__init__(default_configuration_handler_description, experiment)

    def get_default_configuration(self) -> Configuration:
        activated_regions = self.experiment.search_space.get_regions_on_current_level()
        assert len(activated_regions) == 1
        configuration = pd.DataFrame()
        while len(activated_regions) > 0:
            for region in activated_regions:
                for hp in region:
                    temp = hp.get_default()
                    partial_configuration = pd.DataFrame(temp.values(), columns=temp.keys())
                    if configuration.empty:
                        configuration = partial_configuration
                    else:
                        configuration = configuration.join(partial_configuration)
                self.experiment.search_space.next_level()
                activated_regions = self.experiment.search_space.activate_regions(configuration)

        self.experiment.search_space.reset_level()

        mapping_parameters_to_values = configuration.to_dict(orient="records")
        default_configuration = Configuration(mapping_parameters_to_values[0], Configuration.Type.DEFAULT, self.experiment.unique_id)
        return default_configuration
