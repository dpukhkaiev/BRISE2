from typing import Tuple, Dict

from configuration_selection.model.surrogate.surrogate_abs import Surrogate
from tools.reflective_class_import import reflective_class_import


class SurrogateOrchestrator:

    def get_surrogate(self, surrogate_description: Dict, region: Tuple, objectives: Dict) -> Surrogate:
        keys = list(surrogate_description['Instance'].keys())
        assert len(keys) == 1
        feature_name = keys[0]
        surrogate_class = reflective_class_import(class_name=surrogate_description["Instance"][feature_name]["Type"],
                                                  folder_path="configuration_selection/model/surrogate")

        return surrogate_class(surrogate_description, region, objectives)
