from typing import Dict, List

from core_entities.configuration import Configuration
from transfer_learning.multi_task_learning.multi_task_learning_abs import MultiTaskLearning
from transfer_learning.multi_task_learning.mtl_decorator import MultiTaskLearningDecorator


class FewShotDecorator(MultiTaskLearningDecorator):
    def __init__(self, experiment_description: Dict, experiment_id, base_mtl: MultiTaskLearning):
        super().__init__(experiment_description, experiment_id, base_mtl)
        objective_name = list(experiment_description["Context"]["TaskConfiguration"]["Objectives"].keys())[0]  # SO only
        self.is_minimization = experiment_description["Context"]["TaskConfiguration"]["Objectives"][objective_name]["Minimization"]
        self.has_fired = False
        self.is_few_shot = True

    def transfer_configurations(self, similar_experiments: List) -> List[Configuration]:
        """
        Returns the best configuration from the most similar source experiment
        to be directly measured in the target experiment
        :return: Configuration to be directly transferred
        """
        if self.has_fired:
            return []

        base_transferred_configurations = self.base_mtl.transfer_configurations(similar_experiments)
        transferred_configurations = self._filter_configurations(base_transferred_configurations)

        return transferred_configurations

    def _filter_configurations(self, configurations: List[Configuration]) -> List[Configuration]:
        configs_to_transfer: List[Configuration] = []

        if self.is_minimization:
            best_configuration = min(configurations)
        else:
            best_configuration = max(configurations)
        configs_to_transfer.append(best_configuration)
        self.has_fired = True
        return configs_to_transfer
