import random

import pandas as pd
from typing import Dict, Tuple

from configuration_selection.model.surrogate.surrogate_abs import Surrogate
from core_entities.objectives import Objectives


class ModelMock(Surrogate):
    def __init__(self, surrogate_description: Dict, region: Tuple, objectives: Objectives):
        super().__init__(surrogate_description, region, objectives)
        self.multi_objective = surrogate_description['Instance']['ModelMock']['MultiObjective']

    def create(self, features: pd.DataFrame, labels: pd.DataFrame) -> bool:
        return True

    def predict(self, cfg: pd.Series, transform: bool = True) -> pd.DataFrame:
        mapping_predicted_objective: Dict[float, str] = {}
        for o in self.objectives.names:
            mapping_predicted_objective[random.random()] = o
        transformed_prediction = self._transform(mapping_predicted_objective)

        return transformed_prediction

    def predict_batch(self, configurations: pd.DataFrame, transform: bool = True) -> pd.DataFrame:
        # each row's mock value is independently random, so there is nothing to vectorize; each row is
        # predicted on its own, same as predict(), just collected into a single result Dataframe
        predicted = pd.DataFrame()
        for _, cfg in configurations.reset_index(drop=True).iterrows():
            prediction = self.predict(cfg, transform)
            predicted = pd.concat([predicted, prediction], ignore_index=True)
        return predicted

    def _transform(self, mapping_predicted_objective: Dict[float, str]) -> pd.DataFrame:
        """
        Transform a floating point value between 0 and 1 into a DataFrame according to the Objective type.
        :param df: Floating-point value to be transformed.
        :return: Transformed DataFrame.
        """
        transformed_values = pd.DataFrame()  # transform based on the Objective type
        for value, name in mapping_predicted_objective.items():
            objective = self.objectives.by_name(name)
            lower, upper = objective.expected_range
            if objective.data_type == "float":
                transformed_value = lower + value * (upper - lower)
            elif objective.data_type == "int":
                transformed_value = round(lower + value * (upper - lower))
            else:
                raise NotImplementedError  # Objective function types except of numeric are not supported!

            if transformed_values.empty:
                transformed_values = pd.DataFrame(columns=[objective.name])
                transformed_values.loc[0] = transformed_value
            else:
                temp = pd.DataFrame(columns=[objective.name])
                temp.loc[0] = transformed_value
                transformed_values = transformed_values.join(temp)

        return transformed_values
