import logging

from abc import ABC, abstractmethod

class ClusteringAlgorithm(ABC):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def cluster_top_most_similar_experiments(self, similar_experiments: list):
        pass
