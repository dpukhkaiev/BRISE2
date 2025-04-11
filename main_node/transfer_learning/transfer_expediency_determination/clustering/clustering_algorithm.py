import logging
from typing import Dict

from abc import ABC, abstractmethod


class ClusteringAlgorithm(ABC):
    def __init__(self, clustering_description: Dict):
        self.logger = logging.getLogger(__name__)
        self.clustering_description = clustering_description

    @abstractmethod
    def cluster_top_most_similar_experiments(self, similar_experiments: list):
        pass
