import pandas as pd
from typing import Dict, Tuple
from abc import ABC, abstractmethod

from configuration_selection.model.configuration_transformer.configuration_transformer_abs import ConfigurationTransformer


class NominalTransformer(ConfigurationTransformer, ABC):
    def __init__(self, nominal_transformer_description: Dict, relevant_parameters: Tuple):
        super().__init__(nominal_transformer_description, relevant_parameters)
        self.nominal_transformer_description = nominal_transformer_description

    @abstractmethod
    def transform(self, features: pd.DataFrame) -> pd.DataFrame:
        pass

    @abstractmethod
    def inverse_transform(self, transformed_features: pd.DataFrame) -> pd.DataFrame:
        pass
