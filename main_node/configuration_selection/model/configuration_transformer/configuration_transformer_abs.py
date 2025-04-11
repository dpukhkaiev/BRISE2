from abc import ABC, abstractmethod
import pandas as pd
from typing import Tuple, Dict


class ConfigurationTransformer(ABC):
    def __init__(self, configuration_transformer_description: Dict, relevant_parameters: Tuple):
        self.configuration_transformer_description = configuration_transformer_description
        self.relevant_parameters = relevant_parameters
        self.mapping_old_new_features = {}

    @abstractmethod
    def transform(self, features: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms raw values of parameters (features) according to the selected transformer.
        IMPORTANT: the ordering of parameters must preserve
        :param features: raw values of parameters
        :return: transformed features
        """
        pass

    @abstractmethod
    def inverse_transform(self, transformed_features: pd.DataFrame) -> pd.DataFrame:
        pass

    def _inverse_sklearn_transform(self,
                                   transformed_features: pd.DataFrame,
                                   mapping_old_feature_pipeline: Dict) -> pd.DataFrame:
        """
        Helper method for sklearn inverse transformation, which is identical for all parameter types.
        """
        result = pd.DataFrame()
        for old_f, new_f in self.mapping_old_new_features.items():
            if any([f in transformed_features.columns for f in new_f]) is False:
                continue  # some parameters within the mapping can be irrelevant and are skipped
            transformed = mapping_old_feature_pipeline[old_f].inverse_transform(transformed_features[new_f])
            if result.empty:
                result = transformed
            else:
                result = pd.concat([result, transformed])
        return result

    def _filter_relevant_features(self, features: pd.DataFrame) -> pd.DataFrame:
        names = [param.name for param in self.relevant_parameters]
        relevant_feature_names_from_input = []
        for f_n in features.columns:
            if f_n in names:
                relevant_feature_names_from_input.append(f_n)
        return features[relevant_feature_names_from_input]

    def __eq__(self, other):
        return (self.configuration_transformer_description.__eq__(
            other.configuration_transformer_description) and self.relevant_parameters.__eq__(
            other.relevant_parameters) and self.mapping_old_new_features.__eq__(other.mapping_old_new_features))

    def __hash__(self):
        return 17 * hash(self.relevant_parameters) + hash(list(self.configuration_transformer_description.keys())[0])
