import logging
import os

from tools.mongo_dao import MongoDB
from abc import ABC, abstractmethod


class Comparator(ABC):
    def __init__(self, experiment_description: dict, experiment_id: str):
        self.logger = logging.getLogger(__name__)
        self.experiment_description = experiment_description
        self.experiment_id = experiment_id
        self.database = MongoDB(os.getenv("BRISE_DATABASE_HOST"),
                                os.getenv("BRISE_DATABASE_PORT"),
                                os.getenv("BRISE_DATABASE_NAME"),
                                os.getenv("BRISE_DATABASE_USER"),
                                os.getenv("BRISE_DATABASE_PASS"))

    def get_similar_experiments(self, source_experiments: list):
        """
        Template method to identify source experiments that are similar to the target one:
        1. Get source and target labels
        2. Compute similarity metric
        3. Get number of similar experiments (using clustering, static number, etc.)
        :param source_experiments: list
        :return: the list of source experiments to be used for transfer
        """
        metrics = {}
        for source_experiment in source_experiments:
            source_labels, target_labels = self.get_source_and_target_labels(source_experiment)
            if len(source_labels) == 0 or len(target_labels) == 0:
                continue
            metrics[str(source_experiment["Exp_unique_ID"])] = self.compute_metric(source_labels, target_labels)
        sorted_experiments = sorted(metrics.items(), key=lambda x: x[1])
        return sorted_experiments

    @abstractmethod
    def get_source_and_target_labels(self, model):
        pass

    @abstractmethod
    def compute_metric(self, source_labels: list, target_labels: list):
        pass
