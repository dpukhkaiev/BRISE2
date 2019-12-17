from core_entities.configuration import Configuration
from selection.selection_algorithms import get_selector
from default_config_handler.abstract_default_config_handler import AbstractDefaultConfigurationHandler
import logging


class RandomDefaultConfigurationHandler(AbstractDefaultConfigurationHandler):

    def get_default_config(self):
        """
        This method picks random default configuration using specified in Experiment Description Selection algorithm.
        :rtype:Configuration
        """
        selector = get_selector(experiment=self.experiment)
        default_config = selector.get_next_configuration()
        logging.getLogger(__name__).warning(
            "Random Configuration is picked as a default one: %s" % default_config.parameters)
        return default_config
