import os
from abc import ABC, abstractmethod
from typing import Dict, List

from core_entities.configuration import Configuration
from tools.mongo_dao import MongoDB


class MultiTaskLearning(ABC):

    def __init__(self, experiment_description: Dict, experiment_id):
        self.experiment_description = experiment_description
        self.experiment_id = experiment_id
        self.is_few_shot = False
        self.database = MongoDB(os.getenv("BRISE_DATABASE_HOST"),
                                os.getenv("BRISE_DATABASE_PORT"),
                                os.getenv("BRISE_DATABASE_NAME"),
                                os.getenv("BRISE_DATABASE_USER"),
                                os.getenv("BRISE_DATABASE_PASS"))

    @abstractmethod
    def transfer_configurations(self, similar_experiments: List) -> List[Configuration]:
        pass
