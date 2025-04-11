import pandas as pd
from typing import Dict

from configuration_selection.model.value_transformer.value_scalarizator_abs import ValueScalarizator


class WeightedSum(ValueScalarizator):
    def __init__(self, value_transformer_description: Dict, objectives: Dict):
        super().__init__(value_transformer_description, objectives)
        self.weights = value_transformer_description[self.feature_name]["Weights"]

    def transform(self, objective_function_values: pd.DataFrame) -> pd.DataFrame:
        assert len(objective_function_values.columns) == len(self.weights)
        transformed_objective_function_values = objective_function_values.dot(self.weights)
        temp_df = pd.DataFrame()
        if type(transformed_objective_function_values) is pd.Series:
            transformed_objective_function_values = pd.concat([temp_df, transformed_objective_function_values])
            transformed_objective_function_values.rename(columns={0: "Y"}, inplace=True)
        else:
            transformed_objective_function_values.rename(columns={"<unnamed>": "Y"}, inplace=True)

        return transformed_objective_function_values
