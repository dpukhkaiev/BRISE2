from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from default_config_handler.abstract_default_config_handler import AbstractDefaultConfigurationHandler

class AutomodelDefaultConfigurationHandler(AbstractDefaultConfigurationHandler):
    def __init__(self, experiment: Experiment):
        self.experiment = experiment

    def get_default_config(self):    
        """
        This method is applicable if RapidMiner use case is run. In this case default configuration 
        can be defined using `RM Automodel tool <https://docs.rapidminer.com/latest/studio/auto-model>`_

        :rtype:Configuration
        """
        config = []
        hyperparameter_names = self.experiment.search_space.get_hyperparameter_names()
        for __ in hyperparameter_names:
            config.append("defined_by_automodel")
        default_config = Configuration(parameters=config, config_type=Configuration.Type.DEFAULT)
        return default_config
