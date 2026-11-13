from typing import Dict, List


from core_entities.configuration import Configuration
from core_entities.objectives import Objectives
from transfer_learning.multi_task_learning.multi_task_learning_abs import MultiTaskLearning
from transfer_learning.multi_task_learning.mtl_decorator import MultiTaskLearningDecorator


class OnlyBestDecorator(MultiTaskLearningDecorator):
    def __init__(self, experiment_description: Dict, experiment_id, base_mtl: MultiTaskLearning):
        super().__init__(experiment_description, experiment_id, base_mtl)
        # single objective only, required by the feature model
        self.objective = next(iter(Objectives.from_description(experiment_description["Context"]["TaskConfiguration"]["Objectives"])))

    def _filter_configurations(self, configurations: List[Configuration]) -> List[Configuration]:
        """
        Filters configurations better than average.
        :return: Filtered configurations.
        """
        name = self.objective.name
        avg_objective_value = sum([c.results[name] for c in configurations]) / len(configurations)
        if self.objective.minimization:
            configs_to_transfer = list(filter(lambda c: c.results[name] <= avg_objective_value, configurations))
        else:
            configs_to_transfer = list(filter(lambda c: c.results[name] >= avg_objective_value, configurations))
        return configs_to_transfer
