import logging
from abc import ABC, abstractmethod


class ModelPerformanceMetric(ABC):

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def compute(self) -> dict:
        pass
