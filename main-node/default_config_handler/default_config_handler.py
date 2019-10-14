from core_entities.configuration import Configuration
from default_config_handler.abstract_default_config_handler import AbstractDefaultConfigurationHandler

class DefaultConfigurationHandler(AbstractDefaultConfigurationHandler):
    def __init__(self, experiment):
        self.experiment = experiment
        
    def get_default_config(self):    
        """ This method returns default configuration of type Configuration,
        if default configuration is specified correctly by user
        
        :rtype:Configuration
        """
        return Configuration(self.experiment.description["DomainDescription"]["DefaultConfiguration"])
