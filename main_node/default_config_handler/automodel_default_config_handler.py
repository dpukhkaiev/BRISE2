from core_entities.experiment import Experiment
from default_config_handler.abstract_default_config_handler import AbstractDefaultConfigurationHandler

class AutomodelDefaultConfigurationHandler(AbstractDefaultConfigurationHandler):
    def __init__(self, experiment: Experiment):
        super().__init__(experiment)

    def get_default_config(self):
        """
        This method is applicable if RapidMiner use case is run. In this case default configuration
        can be defined using `RM Automodel tool <https://docs.rapidminer.com/latest/studio/auto-model>`_

        :rtype:OrderedDict
        """
        new_default_values = self.experiment.search_space.generate_default()
        for parameter in new_default_values:
            new_default_values[parameter] = "defined_by_automodel"
        return new_default_values
