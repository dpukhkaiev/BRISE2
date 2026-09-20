from typing import Dict, List
from abc import abstractmethod

from core_entities.configuration import Configuration
from transfer_learning.multi_task_learning.multi_task_learning_abs import MultiTaskLearning


class MultiTaskLearningDecorator(MultiTaskLearning):

    def __init__(self, experiment_description: Dict, experiment_id, base_mtl: MultiTaskLearning):
        super().__init__(experiment_description, experiment_id)
        self.base_mtl = base_mtl
        self.is_few_shot = base_mtl.is_few_shot

    def transfer_configurations(self, similar_experiments: List) -> List[Configuration]:
        base_transferred_configurations = self.base_mtl.transfer_configurations(similar_experiments)
        if len(base_transferred_configurations) == 0:
            return []
        return self._filter_configurations(base_transferred_configurations)

    @abstractmethod
    def _filter_configurations(self, configurations: List[Configuration]) -> List[Configuration]:
        pass
