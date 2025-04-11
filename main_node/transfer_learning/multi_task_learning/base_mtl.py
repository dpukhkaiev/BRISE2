from typing import Dict, List

from core_entities.configuration import Configuration
from transfer_learning.multi_task_learning.multi_task_learning_abs import MultiTaskLearning


class BaseMTL(MultiTaskLearning):
    def __init__(self, experiment_description: Dict, experiment_id):
        super().__init__(experiment_description, experiment_id)

    def transfer_configurations(self, similar_experiments: List) -> List[Configuration]:
        """
        Extracts all transferable source configurations.
        :return: list of transferable configurations
        """
        all_samples = []
        for experiment in similar_experiments:
            all_samples.extend(experiment["Samples"])
        transferable_configurations = []

        for sample in all_samples:
            c = Configuration(sample["parameters"], Configuration.Type.TRANSFERRED, self.experiment_id)
            c.results = sample["results"]
            transferable_configurations.append(c)

        return transferable_configurations
