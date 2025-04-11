import pandas as pd
from typing import Dict, Tuple
from abc import ABC, abstractmethod

from configuration_selection.model.configuration_transformer.configuration_transformer_abs import ConfigurationTransformer


class IntegerTransformer(ConfigurationTransformer, ABC):
    def __init__(self, integer_transformer_description: Dict, relevant_parameters: Tuple):
        super().__init__(integer_transformer_description, relevant_parameters)
        self.integer_transformer_description = integer_transformer_description

    @abstractmethod
    def transform(self, features: pd.DataFrame) -> pd.DataFrame:
        pass

    @abstractmethod
    def inverse_transform(self, transformed_features: pd.DataFrame) -> pd.DataFrame:
        pass
