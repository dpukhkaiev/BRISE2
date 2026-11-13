from typing import Dict, List

from core_entities.configuration import Configuration
from core_entities.objectives import Objectives
from transfer_learning.multi_task_learning.multi_task_learning_abs import MultiTaskLearning
from transfer_learning.multi_task_learning.mtl_decorator import MultiTaskLearningDecorator


class FewShotDecorator(MultiTaskLearningDecorator):
    def __init__(self, experiment_description: Dict, experiment_id, base_mtl: MultiTaskLearning):
        super().__init__(experiment_description, experiment_id, base_mtl)
        # single objective only, required by the feature model
        self.objective = next(iter(Objectives.from_description(experiment_description["Context"]["TaskConfiguration"]["Objectives"])))
        self.has_fired = False
        self.is_few_shot = True

    def transfer_configurations(self, similar_experiments: List) -> List[Configuration]:
        if self.has_fired:
            return []
        return super().transfer_configurations(similar_experiments)

    def _filter_configurations(self, configurations: List[Configuration]) -> List[Configuration]:
        """
        Returns the best configuration from the most similar source experiment
        to be directly measured in the target experiment
        :return: Configuration to be directly transferred
        """
        best_configuration = min(configurations, key=lambda c: self.objective.sign * c.results[self.objective.name])
        self.has_fired = True
        return [best_configuration]
