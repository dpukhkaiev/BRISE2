from typing import Tuple

from configuration_selection.model.configuration_transformer.configuration_transformer_abs import ConfigurationTransformer
from tools.reflective_class_import import reflective_class_import


class ConfigurationTransformerOrchestrator:
    def get_configuration_transformer(self, configuration_transformer_description: Tuple, relevant_parameters: Tuple) -> ConfigurationTransformer:
        # TODO long term: move CT types to separate directories -> reflective class import over directories
        feature_name = list(configuration_transformer_description[1].keys())[0]
        configuration_transformer_class = reflective_class_import(configuration_transformer_description[1][feature_name]["Type"],
                                                                  "configuration_selection/model/configuration_transformer")
        return configuration_transformer_class(configuration_transformer_description[1], relevant_parameters)
