from typing import Tuple, Dict

from configuration_selection.model.optimizer.optimizer_abs import Optimizer

from tools.reflective_class_import import reflective_class_import


class OptimizerOrchestrator:
    def get_optimizer(self, optimizer_description: Dict, region: Tuple, objectives: Dict) -> Optimizer:
        keys = list(optimizer_description['Instance'].keys())
        assert len(keys) == 1
        feature_name = keys[0]
        optimizer_class = reflective_class_import(class_name=optimizer_description["Instance"][feature_name]["Type"],
                                                  folder_path="configuration_selection/model/optimizer")

        return optimizer_class(optimizer_description, region, objectives)
