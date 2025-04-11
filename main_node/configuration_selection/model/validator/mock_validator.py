import pandas as pd
from typing import List, Tuple, Dict

from configuration_selection.model.surrogate.surrogate_abs import Surrogate
from configuration_selection.model.validator.validator_abs import Validator


class MockValidator(Validator):
    def __init__(self, validator_description: Dict, region: Tuple, objectives: Dict):
        super().__init__(validator_description, region, objectives)
        self.validator_description = validator_description

    def validate(self, surrogate: Surrogate, features: pd.DataFrame, labels: pd.DataFrame) -> Tuple[bool, float]:
        return True, 0

    def train_test_split(self,
                         features: pd.DataFrame,
                         labels: pd.DataFrame) -> Tuple[List[pd.DataFrame], List[pd.DataFrame], List[pd.DataFrame], List[pd.DataFrame]]:
        return [features], [labels], [features], [labels]
