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
        predicted = pd.DataFrame()
        for i in range(self.sampling_size):
            # sample pd.Series
            configuration = self.sampler.sample()
            configuration_as_series: pd.Series = configuration.iloc[0]
            # predict value
            prediction = surrogate.predict(configuration_as_series)
            evaluated_configuration = configuration.join(prediction)
            predicted = pd.concat([predicted, evaluated_configuration])

        return predicted
