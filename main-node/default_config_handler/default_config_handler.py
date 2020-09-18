from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from default_config_handler.abstract_default_config_handler import AbstractDefaultConfigurationHandler


class DefaultConfigurationHandler(AbstractDefaultConfigurationHandler):
    def __init__(self, experiment: Experiment):
        super().__init__(experiment)

    def get_default_config(self) -> Configuration:
        """ This method returns default configuration,
        if default configuration is specified correctly by user
        
        :rtype:OrderedDict
        """
        return self.experiment.search_space.generate_default()

    def get_new_default_config(self):
        return None