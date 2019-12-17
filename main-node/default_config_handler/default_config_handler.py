from core_entities.configuration import Configuration
from default_config_handler.abstract_default_config_handler import AbstractDefaultConfigurationHandler


class DefaultConfigurationHandler(AbstractDefaultConfigurationHandler):

    def get_default_config(self) -> Configuration:
        """ This method returns default configuration of type Configuration,
        if default configuration is specified correctly by user
        
        :rtype:Configuration
        """
        return self.experiment.search_space.get_default_configuration()
