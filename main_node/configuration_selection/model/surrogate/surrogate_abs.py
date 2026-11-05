import pandas as pd
from typing import Dict, Tuple, Mapping
from abc import ABC, abstractmethod

from configuration_selection.model.configuration_transformer.configuration_transformer_orchestrator import ConfigurationTransformerOrchestrator
from configuration_selection.model.value_transformer.value_transformer_orchestrator import ValueTransformerOrchestrator
from configuration_selection.model.configuration_transformer.configuration_transformer_abs import ConfigurationTransformer
from core_entities.search_space import Hyperparameter, active_mask, find_parameters_activated_within_region


class Surrogate(ABC):
    def __init__(self, surrogate_description: Dict, region: Tuple, objectives: Dict):
        self.surrogate_instance = None
        self.region = region
        self.objectives = objectives
        self.surrogate_description = surrogate_description

        self.feature_name = ""
        if "Instance" in surrogate_description.keys():  # Composite surrogates don't have an Instance as a top level feature
            keys = list(surrogate_description['Instance'].keys())
            assert len(keys) == 1
            self.feature_name = keys[0]

        # Configuration Transformers
        self.configuration_transformer_orchestrator = ConfigurationTransformerOrchestrator()
        self.parameters_activated_within_region = find_parameters_activated_within_region(region)
        self.mapping_config_transformer_parameter: Mapping[ConfigurationTransformer, Tuple[Hyperparameter]] = {}
        for i in surrogate_description.items():
            if "ConfigurationTransformer" in i[0]:
                for ct in i[1].items():
                    relevant_parameters = tuple(filter(lambda r: r.type in ct[0], region))
                    configuration_transformer = self.configuration_transformer_orchestrator.get_configuration_transformer(
                        ct, relevant_parameters, frozenset(hp.name for hp in self.parameters_activated_within_region))
                    self.mapping_config_transformer_parameter[configuration_transformer] = relevant_parameters

        # Value Transformers
        self.value_transformers = []
        self.value_transformer_orchestrator = ValueTransformerOrchestrator()
        self.scalarized = False
        for i in surrogate_description.items():
            if "ValueTransformer" in i[0]:
                for vt in i[1].items():
                    if vt[0] == "ValueScalarizator":
                        self.scalarized = True
                    value_transformer = self.value_transformer_orchestrator.get_value_transformer(vt, objectives)
                    self.value_transformers.append(value_transformer)

        self.multi_objective = False

    @abstractmethod
    def create(self, features: pd.DataFrame, labels: pd.DataFrame) -> bool:
        pass

    @abstractmethod
    def predict(self, configuration: pd.Series, transform: bool = True) -> pd.DataFrame:
        """
        Predict exactly one configuration to be used by the optimizer and validator
        :param configuration: configuration to be predicted
        :param transform: whether to apply the transformation or not, e.g., if transformation is already done by the optimizer
        :return: predicted value(-s) as a Dataframe
        """
        pass

    @abstractmethod
    def predict_batch(self, configurations: pd.DataFrame, transform: bool = True) -> pd.DataFrame:
        """
        Predict several configurations at once, instead of one at a time via predict(). Intended for optimizers
        that evaluate many candidates per optimize() call (e.g. random search), where batching the predictions
        can be significantly cheaper than calling predict() once per candidate.
        :param configurations: configurations to be predicted, one per row
        :param transform: whether to apply the transformation or not, e.g., if transformation is already done by the optimizer
        :return: predicted value(-s) as a Dataframe, one row per input configuration, in the same row order,
        with a default RangeIndex (0..n-1)
        """
        pass

    def _write_inactive_values(self, features: pd.DataFrame) -> pd.DataFrame:
        """
        Write the inactive value into the cells of inactive parameters, if the region has any.
        :param features: configurations, one per row, with a column per parameter; a missing parameter holds NaN.
        :return: features with the inactive value in the cells of inactive parameters.
        """
        if not self.parameters_activated_within_region:
            return features
        mask = active_mask(features, [hp.activation_condition for hp in self.parameters_activated_within_region])
        features = features.copy()
        for hp in self.parameters_activated_within_region:
            if hp.name in features.columns:
                inactive = ~mask[hp.name]
                if inactive.any():
                    features[hp.name] = features[hp.name].astype(object)
                    features.loc[inactive, hp.name] = hp.inactive_value()
        return features

    def _transform_configuration(self, features: pd.DataFrame) -> pd.DataFrame:
        features = self._write_inactive_values(features.reset_index(drop=True))
        if len(self.mapping_config_transformer_parameter) > 0:
            transformed_names = sum([[hp.name for hp in p] for p in self.mapping_config_transformer_parameter.values()], [])
            transformed_features = pd.DataFrame()
            for f_name in features.columns:
                if f_name in transformed_names:
                    for ct, p in self.mapping_config_transformer_parameter.items():
                        for hp in p:
                            if hp.name == f_name:
                                transformed_relevant_features = ct.transform(pd.DataFrame(features.loc[:, hp.name]))
                                if transformed_features.empty:
                                    transformed_features = transformed_relevant_features
                                else:
                                    transformed_features = transformed_features.join(transformed_relevant_features)
                else:
                    if transformed_features.empty:
                        transformed_features = pd.DataFrame(features.loc[:, f_name])
                    else:
                        transformed_features = transformed_features.join(pd.DataFrame(features.loc[:, f_name]))
        else:
            transformed_features = features
        return transformed_features

    def _transform_values(self, labels: pd.DataFrame) -> pd.DataFrame:
        transformed_labels = pd.DataFrame()
        if len(self.value_transformers) > 0:
            for vt in self.value_transformers:
                if transformed_labels.empty:
                    transformed_labels = vt.transform(labels)
                else:
                    transformed_labels = vt.transform(transformed_labels)
        else:
            transformed_labels = labels
        return transformed_labels
