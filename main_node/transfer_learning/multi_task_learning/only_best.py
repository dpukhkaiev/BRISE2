from typing import Dict, List


from core_entities.configuration import Configuration
from transfer_learning.multi_task_learning.multi_task_learning_abs import MultiTaskLearning
from transfer_learning.multi_task_learning.mtl_decorator import MultiTaskLearningDecorator


class OnlyBestDecorator(MultiTaskLearningDecorator):
    def __init__(self, experiment_description: Dict, experiment_id, base_mtl: MultiTaskLearning):
        super().__init__(experiment_description, experiment_id, base_mtl)
        self.objective_name = list(experiment_description["Context"]["TaskConfiguration"]["Objectives"].keys())[0]  # SO only
        self.is_minimization = experiment_description["Context"]["TaskConfiguration"]["Objectives"][self.objective_name][
            "Minimization"]

    def _filter_configurations(self, configurations: List[Configuration]) -> List[Configuration]:
        """
        Filters configurations better than average.
        :return: Filtered configurations.
        """
        avg_objective_value = sum([c.results[self.objective_name] for c in configurations]) / len(configurations)
        if self.is_minimization:
            configs_to_transfer = list(filter(lambda c: c.results[self.objective_name] <= avg_objective_value, configurations))
        else:
            configs_to_transfer = list(filter(lambda c: c.results[self.objective_name] >= avg_objective_value, configurations))
        return configs_to_transfer
