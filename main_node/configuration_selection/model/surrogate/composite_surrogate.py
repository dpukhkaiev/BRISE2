import pandas as pd
from typing import Tuple

from configuration_selection.model.surrogate.surrogate_abs import Surrogate


class CompositeSurrogate(Surrogate):
    def __init__(self, surrogates: Tuple[Surrogate], region: Tuple):
        self.surrogates = surrogates
        objectives = {}
        surrogate_description = {}
        for s in surrogates:
            surrogate_description[s.feature_name] = s.surrogate_description
            for o, o_value in s.objectives.items():
                objectives[o] = o_value

        super().__init__(surrogate_description, region, objectives)
        self.multi_objective = True

    def create(self, features: pd.DataFrame, labels: pd.DataFrame) -> bool:
        is_built = []
        for s in self.surrogates:
            i_b = s.create(features, labels[list(s.objectives.keys())])
            is_built.append(i_b)
        return all(is_built) is True

    def predict(self, cfg: pd.Series, transform: bool = True) -> pd.DataFrame:
        result = pd.DataFrame()

        for s in self.surrogates:
            if result.empty:
                result = s.predict(cfg, transform)
            else:
                temp = s.predict(cfg, transform)
                result = result.join(temp)
        return result
