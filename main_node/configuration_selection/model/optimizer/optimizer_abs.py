import numpy as np
import pandas as pd
import pygmo as pg
from typing import Dict, List, Tuple, Mapping
from abc import ABC, abstractmethod

from configuration_selection.model.value_transformer.value_transformer_orchestrator import ValueTransformerOrchestrator
from configuration_selection.model.configuration_transformer.configuration_transformer_abs import ConfigurationTransformer
from configuration_selection.model.surrogate.surrogate_abs import Surrogate
from configuration_selection.model import configuration_transformation
from core_entities.search_space import Hyperparameter


class Optimizer(ABC):
    def __init__(self, optimizer_description: Dict, region: Tuple, objectives: Dict):
        self.region = region
        self.objectives = objectives
        self.feature_name = list(optimizer_description['Instance'].keys())[0]
        self.optimizer_description = optimizer_description

        # Configuration Transformers
        self.mapping_config_transformer_parameter: Mapping[ConfigurationTransformer, Tuple[Hyperparameter]] = (
            configuration_transformation.build_transformers(optimizer_description, region))

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
        :return: a list of evaluated configurations, sorted by their quality, the best first.
        """
        pass

    def _get_direction_signs(self, label_columns: List[str]) -> np.ndarray:
        """
        Gives the direction of each column as a sign.
        :param label_columns: columns holding the (value-transformed) predictions of candidates: objective names, or the
        single column produced by a value transformer.
        :return: +1 for a column to be minimized and -1 for one to be maximized, so that multiplying a column by its
        sign makes it a column to be minimized. A column that is not an objective follows the direction of the first
        objective.
        """
        first_objective = next(iter(self.objectives.values()))
        return np.array([1.0 if self.objectives.get(column, first_objective)["Minimization"] else -1.0
                         for column in label_columns])

    def _rank_candidates(self, candidates: pd.DataFrame, label_columns: List[str]) -> pd.DataFrame:
        """
        Sorts candidates by their predicted quality, the best first, each column in its own direction.
        :param candidates: parameter values of candidates, followed by their predictions.
        :param label_columns: names of the columns that hold the predictions to rank: one per objective,
        or the single column of a value transformer.
        :return: the same candidates, reordered, with a default index.
        """
        if candidates.empty:
            return candidates
        values_to_minimize = candidates[label_columns].to_numpy(dtype=float) * self._get_direction_signs(label_columns)
        if len(label_columns) == 1:
            order = np.argsort(values_to_minimize[:, 0], kind="stable")
        else:
            order = pg.sort_population_mo(values_to_minimize.tolist())
        return candidates.iloc[order].reset_index(drop=True)

    def _transform_configuration(self, features: pd.DataFrame) -> pd.DataFrame:
        return configuration_transformation.transform(features, self.mapping_config_transformer_parameter)

    def _inverse_transform_configuration(self, optimized_features: pd.DataFrame) -> pd.DataFrame:
        return configuration_transformation.inverse_transform(optimized_features, self.mapping_config_transformer_parameter)

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
