from core_entities.configuration import Configuration
from selection.selection_algorithms import get_selector
from default_config_handler.abstract_default_config_handler import AbstractDefaultConfigurationHandler
import logging

class RandomDefaultConfigurationHandler(AbstractDefaultConfigurationHandler):
    def __init__(self, experiment):
        self.experiment = experiment
        self.logger = logging.getLogger(__name__)

    def get_default_config(self):    
        """
        This method picks random default configuration from selector
        
        :rtype:Configuration
        """ 
        selector = get_selector(experiment = self.experiment)
        default_config = Configuration(selector.get_next_configuration())
        self.logger.warning("Random Configuration is picked as a default one: %s" % default_config.get_parameters())
        return default_config
