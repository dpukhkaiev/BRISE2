from typing import Mapping

import pandas as pd

from model.model_abs import Model
from selection.description_selection import description_selection


class ModelMock(Model):
    """
    Utilization of Selection Algorithm only instead of a surrogate model
    """
    def build_model(
            self, features: pd.DataFrame, labels: pd.DataFrame, features_description: Mapping, is_minimization: bool
    ) -> bool:
        self.features_description = features_description
        return True

    def predict(self) -> pd.DataFrame:
        generated_cfg = description_selection(self.features_description)
        return pd.DataFrame(generated_cfg)
