from copy import deepcopy
from random import shuffle
from typing import Dict, List

from core_entities.configuration import Configuration
from transfer_learning.multi_task_learning.multi_task_learning_abs import MultiTaskLearning
from transfer_learning.multi_task_learning.mtl_decorator import MultiTaskLearningDecorator


class ShuffleDecorator(MultiTaskLearningDecorator):
    def __init__(self, experiment_description: Dict, experiment_id, base_mtl: MultiTaskLearning):
        super().__init__(experiment_description, experiment_id, base_mtl)

    def _filter_configurations(self, configurations: List[Configuration]) -> List[Configuration]:
        """
        Shuffles list of configurations for transferring.
        :return: shuffled list of configurations.
        """
        configs_to_transfer = deepcopy(configurations)
        shuffle(configs_to_transfer)
        return configs_to_transfer
