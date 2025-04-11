from typing import Dict, List

from core_entities.configuration import Configuration
from transfer_learning.multi_task_learning.multi_task_learning_abs import MultiTaskLearning
from transfer_learning.multi_task_learning.mtl_decorator import MultiTaskLearningDecorator


class OldNewRatioDecorator(MultiTaskLearningDecorator):
    def __init__(self, experiment_description: Dict, experiment_id, base_mtl: MultiTaskLearning):
        super().__init__(experiment_description, experiment_id, base_mtl)
        self.old_new_configs_ratio = self.experiment_description["TransferLearning"]["MultiTaskLearning"]["Filters"][
            "OldNewRatio"]["OldNewConfigsRatio"]

    def transfer_configurations(self, similar_experiments: List) -> List[Configuration]:
        """
        Filters configurations according to the given ratio of old and new configurations.
        :return: Filtered configurations.
        """

        base_transferred_configurations = self.base_mtl.transfer_configurations(similar_experiments)
        transferred_configurations = self._filter_configurations(base_transferred_configurations)

        return transferred_configurations

    def _filter_configurations(self, configurations: List[Configuration]) -> List[Configuration]:
        measured_configurations = self.database.get_records_by_experiment_id("Configuration", self.experiment_id)
        number_of_configs_to_transfer = round(len(measured_configurations) * self.old_new_configs_ratio)
        configs_to_transfer = configurations[:number_of_configs_to_transfer]
        return configs_to_transfer
