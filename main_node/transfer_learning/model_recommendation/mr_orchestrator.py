import logging
from typing import Dict

from tools.reflective_class_import import reflective_class_import
from transfer_learning.model_recommendation.model_recommendation_abs import ModelRecommendation


class ModelRecommendationOrchestrator:

    @staticmethod
    def get_mr_module(experiment_description: Dict, experiment_id) -> ModelRecommendation:
        """
        Constructs an instance of model recommendation module according to the experiment description.
        """
        logger = logging.getLogger(__name__)

        keys = list(experiment_description["TransferLearning"]["ModelRecommendation"].keys())
        assert len(keys) == 1
        feature_name = keys[0]

        mr_class = reflective_class_import(class_name=experiment_description["TransferLearning"]["ModelRecommendation"][feature_name]["Type"],
                                           folder_path="transfer_learning/model_recommendation")
        mr = mr_class(experiment_description, experiment_id)
        logger.info(f"Assigned {feature_name} model recommendation approach.")

        return mr
