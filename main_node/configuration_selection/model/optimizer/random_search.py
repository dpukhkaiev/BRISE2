from typing import Tuple, Dict

import pandas as pd

from configuration_selection.model.optimizer.optimizer_abs import Optimizer
from configuration_selection.model.surrogate.surrogate_abs import Surrogate
from configuration_selection.sampling.mersenne_twister import MersenneTwister
from core_entities.objectives import Objectives


class RandomSearch(Optimizer):
    def __init__(self, optimizer_description: Dict, region: Tuple, objectives: Objectives):
        super().__init__(optimizer_description, region, objectives)
        self.sampling_size = optimizer_description["Instance"][self.feature_name]["SamplingSize"]
        self.sampler = MersenneTwister({}, region)

    def optimize(self, surrogate: Surrogate) -> pd.DataFrame:
        """
        :returns: pd.Dataframe: (n,m), where n is sampling size and m the number of parameters, followed by the
        predictions after the optimizer's value transformers. The best candidate comes first.
        """
        sampled = [self.sampler.sample() for _ in range(self.sampling_size)]
        if not sampled:
            return pd.DataFrame()

        sampled_configurations = pd.concat(sampled, ignore_index=True)
        predicted_values = surrogate.predict_batch(sampled_configurations)
        labels = self._transform_values(predicted_values)
        if len(self.value_transformers) > 0:
            names = ["Y"] if surrogate.scalarized else self.objectives.names
            if len(names) == len(labels.columns):
                labels.columns = names

        predicted = sampled_configurations.join(labels)
        return self._rank_candidates(predicted, list(labels.columns))
