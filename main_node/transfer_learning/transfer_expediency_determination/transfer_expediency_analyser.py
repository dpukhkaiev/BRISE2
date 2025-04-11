import logging
import os

from abc import ABC, abstractmethod
from tools.mongo_dao import MongoDB
from typing import List


class TransferExpediencyAnalyser(ABC):
    def __init__(self, ted_description: dict, experiment_id: str):
        self.logger = logging.getLogger(__name__)
        self.ted_description = ted_description
        self.experiment_id = experiment_id
        self.similar_experiments = []
        self.were_similar_experiments_found = False
        self.feature_name = list(self.ted_description.keys())[0]

        self.database = MongoDB(os.getenv("BRISE_DATABASE_HOST"),
                                os.getenv("BRISE_DATABASE_PORT"),
                                os.getenv("BRISE_DATABASE_NAME"),
                                os.getenv("BRISE_DATABASE_USER"),
                                os.getenv("BRISE_DATABASE_PASS"))

    @abstractmethod
    def analyse_experiments_similarity(self) -> List:
        """
        Extracts source experiments from the DB. Returns the list of similar source experiments
        :return: list of similar experiments
        """
        pass
