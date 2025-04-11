import pickle
from typing import Dict, List, Union, Tuple

from transfer_learning.model_recommendation.model_recommendation_abs import ModelRecommendation
from configuration_selection.model.model import Model
from core_entities.search_space import Hyperparameter


class FewShotRecommendation(ModelRecommendation):
    def __init__(self, experiment_description: Dict, experiment_id):
        super().__init__(experiment_description, experiment_id)
        self.was_model_transferred = False
        self.is_few_shot = True

    def recommend_best_model(self, similar_experiments: List) -> Union[Dict[Tuple[Hyperparameter], Model], None]:
        if self.was_model_transferred:
            return None
        transferred_models = []
        for experiment in similar_experiments:
            if self.were_models_dumped(experiment["Models_dumps"]):
                for hierarchical_models_dump in experiment["Models_dumps"]:
                    hierarchical_model = {}
                    for model in hierarchical_models_dump:
                        m: Model = pickle.loads(model)
                        hierarchical_model[m.region] = m
                    transferred_models.append(hierarchical_model)
                break
        if len(transferred_models) == 0:
            return None
        self.was_model_transferred = True
        last_model = transferred_models[len(transferred_models) - 1]
        return last_model

    @staticmethod
    def were_models_dumped(model_dumps: list):
        if len(model_dumps) == 0:
            return False
        were_models_dumped = True
        for model_dump in model_dumps:
            if model_dump is None:
                were_models_dumped = False
        return were_models_dumped
