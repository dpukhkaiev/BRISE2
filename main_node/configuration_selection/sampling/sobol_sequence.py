__doc__ = """
    Sampling strategy that uses Sobol Sequence generator."""
import pandas as pd
from typing import Mapping, Tuple
from scipy.stats.qmc import Sobol

from configuration_selection.sampling.selection_algorithm_abs import SamplingStrategy
from core_entities.search_space import Hyperparameter


class SobolSequence(SamplingStrategy):
    def __init__(self, parameters: Mapping, region: Tuple[Hyperparameter]):
        """
        Sampling strategy that uses Sobol Sequence generator.
        """
        super().__init__(parameters, region)
        dimensionality = len(region)
        self.seed = parameters["Seed"]
        self.sampler = Sobol(d=dimensionality, scramble=False, seed=self.seed)
        self.sequence = self.sampler.random_base2(20)  # sample 1kk points TODO fix for larger values
        self.index = 0

    def sample(self) -> pd.DataFrame:
        sampled_values = self.sequence[self.index]
        sampled_values = sampled_values.reshape(1, len(sampled_values))  # reshape to 1 row, X columns

        result = self.transform(sampled_values)
        self.index += 1
        return result
