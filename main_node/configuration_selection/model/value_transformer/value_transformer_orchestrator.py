from typing import Tuple, Dict

from configuration_selection.model.value_transformer.value_transformer_abs import ValueTransformer
from tools.reflective_class_import import reflective_class_import


class ValueTransformerOrchestrator():

    def get_value_transformer(self, value_transformer_description: Tuple, objectives: Dict) -> ValueTransformer:
        feature_name = list(value_transformer_description[1].keys())[0]
        value_transformer_class = reflective_class_import(value_transformer_description[1][feature_name]["Type"],
                                                          "configuration_selection/model/value_transformer")
        return value_transformer_class(value_transformer_description[1], objectives)
