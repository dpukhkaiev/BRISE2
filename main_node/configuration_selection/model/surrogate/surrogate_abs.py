import pandas as pd
from typing import Dict, Tuple, Mapping
from abc import ABC, abstractmethod

from configuration_selection.model.value_transformer.value_transformer_orchestrator import ValueTransformerOrchestrator
from configuration_selection.model.configuration_transformer.configuration_transformer_abs import ConfigurationTransformer
from configuration_selection.model import configuration_transformation
from core_entities.search_space import Hyperparameter, find_parameters_activated_within_region


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
        self.parameters_activated_within_region = find_parameters_activated_within_region(region)
        self.mapping_config_transformer_parameter: Mapping[ConfigurationTransformer, Tuple[Hyperparameter]] = (
            configuration_transformation.build_transformers(
                surrogate_description, region, frozenset(hp.name for hp in self.parameters_activated_within_region)))

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

    def _transform_configuration(self, features: pd.DataFrame) -> pd.DataFrame:
        return configuration_transformation.transform(
            features, self.mapping_config_transformer_parameter, self.parameters_activated_within_region)

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
