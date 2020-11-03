from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import List, Mapping, Union

import pandas as pd
from core_entities.search_space import Hyperparameter


class Model(ABC):

    def __init__(self, parameters: Mapping):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.parameters = parameters
        self.label_objectives: List[bool] = []
        self.is_built: bool = False
        self.model = None
        self.features_description: OrderedDict[str, OrderedDict[str, Union[Hyperparameter, list]]] = None

    @abstractmethod
    def build_model(
            self, features: pd.DataFrame, labels: pd.DataFrame, features_description: Mapping, is_minimization: bool
    ) -> bool:
        pass

    @abstractmethod
    def predict(self) -> pd.DataFrame:
        pass
