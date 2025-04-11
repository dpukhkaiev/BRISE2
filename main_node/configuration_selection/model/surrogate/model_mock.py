import random

import pandas as pd
from typing import Dict, Tuple

from configuration_selection.model.surrogate.surrogate_abs import Surrogate


class ModelMock(Surrogate):
    def __init__(self, surrogate_description: Dict, region: Tuple, objectives: Dict):
        super().__init__(surrogate_description, region, objectives)
        self.multi_objective = surrogate_description['Instance']['ModelMock']['MultiObjective']

    def create(self, features: pd.DataFrame, labels: pd.DataFrame) -> bool:
        return True

    def predict(self, cfg: pd.Series, transform: bool = True) -> pd.DataFrame:
        mapping_predicted_objective: Dict[float, str] = {}
        for o in self.objectives:
            mapping_predicted_objective[random.random()] = o
        transformed_prediction = self._transform(mapping_predicted_objective)

        return transformed_prediction

    def _transform(self, mapping_predicted_objective: Dict[float, str]) -> pd.DataFrame:
        """
        Transform a floating point value between 0 and 1 into a DataFrame according to the Objective type.
        :param df: Floating-point value to be transformed.
        :return: Transformed DataFrame.
        """
        # TODO add a separate objective class like for hypeparameters
        transformed_values = pd.DataFrame()  # transform based on the Objective type
        for value, objective in mapping_predicted_objective.items():
            if self.objectives[objective]["DataType"].__eq__("float"):
                transformed_value = self.objectives[objective]["MinExpectedValue"] + value * (self.objectives[objective]["MaxExpectedValue"] - self.objectives[objective]["MinExpectedValue"])
            elif self.objectives[objective]["DataType"].__eq__("int"):
                transformed_value = round(self.objectives[objective]["MinExpectedValue"] + value * (self.objectives[objective]["MaxExpectedValue"] - self.objectives[objective]["MinExpectedValue"]))
            else:
                raise NotImplementedError  # Objective function types except of numeric are not supported!

            if transformed_values.empty:
                transformed_values = pd.DataFrame(columns=[self.objectives[objective]["Name"]])
                transformed_values.loc[0] = transformed_value
            else:
                temp = pd.DataFrame(columns=[self.objectives[objective]["Name"]])
                temp.loc[0] = transformed_value
                transformed_values = transformed_values.join(temp)

        return transformed_values
