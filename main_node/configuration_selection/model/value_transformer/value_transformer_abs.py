import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict
from core_entities.objectives import Objectives


class ValueTransformer(ABC):
    def __init__(self, value_transformer_description: Dict, objectives: Objectives):
        self.value_transformer_description = value_transformer_description
        self.feature_name = list(value_transformer_description.keys())[0]
        self.objectives = objectives

    @abstractmethod
    def transform(self, objective_function_values: pd.DataFrame) -> pd.DataFrame:
        pass
