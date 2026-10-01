from typing import Tuple, Dict

import pandas as pd

from configuration_selection.model.optimizer.optimizer_abs import Optimizer
from configuration_selection.model.surrogate.surrogate_abs import Surrogate
from configuration_selection.sampling.mersenne_twister import MersenneTwister


class RandomSearch(Optimizer):
    def __init__(self, optimizer_description: Dict, region: Tuple, objectives: Dict):
        super().__init__(optimizer_description, region, objectives)
        self.sampling_size = optimizer_description["Instance"][self.feature_name]["SamplingSize"]
        self.sampler = MersenneTwister({}, region)

    def optimize(self, surrogate: Surrogate) -> pd.DataFrame:
        """
        :returns: pd.Dataframe: (n,m), where n is sampling size and m the number of parameters
        """
        # sample every candidate first, then predict all of them in one batched call instead of
        # sampling_size separate predict() calls - cheaper whenever the surrogate can vectorize (see
        # Surrogate.predict_batch on each surrogate implementation)
        sampled = [self.sampler.sample() for _ in range(self.sampling_size)]
        if not sampled:
            return pd.DataFrame()

        sampled_configurations = pd.concat(sampled, ignore_index=True)
        predicted_values = surrogate.predict_batch(sampled_configurations)
        predicted = sampled_configurations.join(predicted_values)

        return predicted
