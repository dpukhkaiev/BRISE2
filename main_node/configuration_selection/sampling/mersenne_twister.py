import random
import pandas as pd
import numpy as np
from typing import Mapping, Tuple

from configuration_selection.sampling.selection_algorithm_abs import SamplingStrategy
from core_entities.search_space import Hyperparameter


class MersenneTwister(SamplingStrategy):
    def __init__(self, parameters: Mapping, region: Tuple[Hyperparameter]):
        """
        Selection algorithm that uses Mersenne Twister pseudo-random generator. <https://docs.python.org/3/library/random.html>
        """
        super().__init__(parameters, region)

    def sample(self) -> pd.DataFrame:

        sampled_values = []
        for i in range(len(self.region)):
            sampled_values.append(random.random())
        sampled_values = np.array(sampled_values).reshape(1, len(self.region))

        result = self.transform(sampled_values)
        return result
