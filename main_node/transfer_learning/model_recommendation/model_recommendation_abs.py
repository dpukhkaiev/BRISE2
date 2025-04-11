import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Union, Tuple

from core_entities.search_space import Hyperparameter
from configuration_selection.model.model import Model
from tools.mongo_dao import MongoDB


class ModelRecommendation(ABC):

    def __init__(self, experiment_description: Dict, experiment_id):
        self.experiment_description = experiment_description
        self.experiment_id = experiment_id
        self.feature_name = list(self.experiment_description["TransferLearning"]["ModelRecommendation"].keys())[0]
        self.is_few_shot = False
        self.logger = logging.getLogger(__name__)
        self.database = MongoDB(os.getenv("BRISE_DATABASE_HOST"),
                                os.getenv("BRISE_DATABASE_PORT"),
                                os.getenv("BRISE_DATABASE_NAME"),
                                os.getenv("BRISE_DATABASE_USER"),
                                os.getenv("BRISE_DATABASE_PASS"))

    @abstractmethod
    def recommend_best_model(self, similar_experiments: List) -> Union[Dict[Tuple[Hyperparameter], Model], None]:
        """
       Get the most relevant model from the most similar experiment (if it is possible)
       to use it within the target experiment.
       :return: a mapping of region to model to be used by predictor
       """
        pass
