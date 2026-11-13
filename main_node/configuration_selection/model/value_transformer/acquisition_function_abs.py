import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict

from configuration_selection.model.value_transformer.value_transformer_abs import ValueTransformer
from core_entities.objectives import Objectives


class AcquisitionFunction(ValueTransformer, ABC):
    def __init__(self, value_transformer_description: Dict, objectives: Objectives):
        super().__init__(value_transformer_description, objectives)

    @abstractmethod
    def transform(self, objective_function_values: pd.DataFrame) -> pd.DataFrame:
        pass
