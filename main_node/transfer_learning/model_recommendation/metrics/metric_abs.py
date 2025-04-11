import logging
from abc import ABC, abstractmethod
from typing import List, Dict


class ModelPerformanceMetric(ABC):

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def compute(self,
                improvement_curve: List,
                prediction_infos: List,
                start_index: int,
                end_index: int,
                multi_model: bool) -> Dict:
        pass
