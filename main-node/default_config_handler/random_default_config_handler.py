from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from selection.selection_algorithms import get_selector
from default_config_handler.abstract_default_config_handler import AbstractDefaultConfigurationHandler
import logging
from collections import OrderedDict


class RandomDefaultConfigurationHandler(AbstractDefaultConfigurationHandler):
    def __init__(self, experiment: Experiment):
        super().__init__(experiment)

    def get_default_config(self):
        """
        This method picks random default configuration using specified in Experiment Description Selection algorithm.
        :rtype:OrderedDict
        """
        new_default_values = OrderedDict()
        while not self.experiment.search_space.validate(new_default_values, is_recursive=True):
                        self.experiment.search_space.generate(new_default_values)
        logging.getLogger(__name__).warning(
            "Random Configuration is picked as a default one: %s" % new_default_values)
        return new_default_values
