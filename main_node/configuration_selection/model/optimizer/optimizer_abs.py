import pandas as pd
from typing import Dict, Tuple, Mapping
from abc import ABC, abstractmethod

from configuration_selection.model.configuration_transformer.configuration_transformer_orchestrator import ConfigurationTransformerOrchestrator
from configuration_selection.model.value_transformer.value_transformer_orchestrator import ValueTransformerOrchestrator
from configuration_selection.model.configuration_transformer.configuration_transformer_abs import ConfigurationTransformer
from configuration_selection.model.surrogate.surrogate_abs import Surrogate
from core_entities.search_space import Hyperparameter


class Optimizer(ABC):
    def __init__(self, optimizer_description: Dict, region: Tuple, objectives: Dict):
        self.region = region
        self.objectives = objectives
        self.feature_name = list(optimizer_description['Instance'].keys())[0]
        self.optimizer_description = optimizer_description

        # Configuration Transformers
        self.configuration_transformer_orchestrator = ConfigurationTransformerOrchestrator()
        self.mapping_config_transformer_parameter: Mapping[ConfigurationTransformer, Tuple[Hyperparameter]] = {}
        for i in optimizer_description.items():
            if "ConfigurationTransformer" in i[0]:
                for ct in i[1].items():
                    relevant_parameters = tuple(filter(lambda r: r.type in ct[0], region))
                    configuration_transformer = (self.configuration_transformer_orchestrator.
                                                 get_configuration_transformer(ct, relevant_parameters))
                    self.mapping_config_transformer_parameter[configuration_transformer] = relevant_parameters

        # Value Transformers
        self.value_transformers = []
        self.scalarized = False
        self.value_transformer_orchestrator = ValueTransformerOrchestrator()
        for i in optimizer_description.items():
            if "ValueTransformer" in i[0]:
                for vt in i[1].items():
                    if vt[0] == "ValueScalarizator":
                        self.scalarized = True
                    value_transformer = self.value_transformer_orchestrator.get_value_transformer(vt, objectives)
                    self.value_transformers.append(value_transformer)

    @abstractmethod
    def optimize(self, surrogate: Surrogate) -> pd.DataFrame:
        """
        :param surrogate: surrogate used for evaluation.
        :return: a list of evaluated configurations, sorted by their quality.
        """
        pass

    def _resolve_configuration_transformers(self, surrogate: Surrogate) -> Tuple[bool, bool]:
        """
        :param surrogate: surrogate used for evaluation.
        :return: True if surrogate needs to transform a configuration on its own; and
        True if optimizer needs to inverse transform a configuration before passing it to surrogate.
        """
        inverse_transform_optimizer = False
        transform_surrogate = False

        if (len(surrogate.mapping_config_transformer_parameter.keys()) == 0 and len(
                self.mapping_config_transformer_parameter.keys()) > 0):
            inverse_transform_optimizer = True
        elif (len(surrogate.mapping_config_transformer_parameter.keys()) > 0 and len(
                self.mapping_config_transformer_parameter.keys()) == 0):
            transform_surrogate = True
        elif not self.mapping_config_transformer_parameter.__eq__(surrogate.mapping_config_transformer_parameter):
            inverse_transform_optimizer = True
            transform_surrogate = True

        return transform_surrogate, inverse_transform_optimizer

    def _transform_configuration(self, features: pd.DataFrame) -> pd.DataFrame:
        features = features.reset_index(drop=True)
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

    def _inverse_transform_configuration(self, optimized_features: pd.DataFrame) -> pd.DataFrame:
        result = pd.DataFrame()
        involved_features = set()  # features involved in configuration transformers
        for new_hp_name in optimized_features.columns:
            for ct, params in self.mapping_config_transformer_parameter.items():
                for old_f, new_f in ct.mapping_old_new_features.items():
                    if new_hp_name not in new_f:
                        continue
                    else:
                        inverse_transformed = ct.inverse_transform(
                            optimized_features[ct.mapping_old_new_features[old_f]])
                        if result.empty:
                            result = inverse_transformed
                        elif inverse_transformed.columns[0] not in result.columns:
                            result = result.join(inverse_transformed)
                        involved_features.add(new_hp_name)
            if new_hp_name not in involved_features:  # parameter not in configuration transformers
                if result.empty:
                    temp_df = optimized_features.copy()
                    temp_df = temp_df[[new_hp_name]]
                    result = temp_df
                elif new_hp_name not in result.columns:
                    result = result.join(optimized_features[new_hp_name])

        return result

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
