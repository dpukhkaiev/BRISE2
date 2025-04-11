from default_config_handler.default_configuration_handler_abs import DefaultConfigurationHandler
from default_config_handler.basic_default_config_handler import BasicDefaultConfigurationHandler
from core_entities.experiment import Experiment
from tools.reflective_class_import import reflective_class_import


class DefaultConfigHandlerOrchestrator():

    def get_default_configuration_handler(self, experiment: Experiment) -> DefaultConfigurationHandler:
        if "DefaultConfigurationHandler" in experiment.description.keys():
            default_configuration_handler_description = experiment.description["DefaultConfigurationHandler"]
            keys = list(default_configuration_handler_description.keys())
            assert len(keys) == 1
            feature_name = keys[0]
            default_configuration_handler_class = reflective_class_import(class_name=default_configuration_handler_description[feature_name]["Type"],
                                                     folder_path="default_config_handler")
            return default_configuration_handler_class(default_configuration_handler_description[feature_name],
                                                       experiment)
        else:
            return BasicDefaultConfigurationHandler({}, experiment)
