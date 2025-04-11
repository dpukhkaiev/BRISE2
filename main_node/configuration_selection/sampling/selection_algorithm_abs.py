__doc__ = """
    Abstract class for creation of selection algorithm with needed methods and fields for ."""
import logging
import pandas as pd
import numpy as np

from abc import ABC, abstractmethod
from typing import Mapping
from typing import Tuple

from core_entities.search_space import Hyperparameter


class SamplingStrategy(ABC):

    def __init__(self, parameters: Mapping, region: Tuple[Hyperparameter]):
        """
        :param parameters: Mapping of internal parameters of the sampling strategy.
        :param region: Tuple[Hyperparameter] region of Hyperparameters which is handled by the sampling strategy.
        """
        self.logger = logging.getLogger(__name__)
        self.parameters = parameters  # internal parameters
        self.region = region
        self.names = [r.name for r in self.region]

    @abstractmethod
    def sample(self) -> pd.DataFrame:
        """
        An abstract sampling method.
        Returns a DataFrame with sampled (partial) configuration.
        """

    def transform(self, df: np.array) -> pd.DataFrame:
        """
        Transform a floating point value between 0 and 1 into a DataFrame according to the Hyperparameter type.
        :param df: Floating-point value to be transformed.
        :return: Transformed DataFrame.
        """

        transformed_values = []  # transform based on the Hyperparameter type
        it = np.nditer(df, flags=['f_index'])  # safe iterator for ndarrays
        for sampled_value in it:
            transformed_values.append(self.region[it.index].transform(sampled_value))

        transformed_values_np = np.array(transformed_values, dtype=object)
        transformed_values_np = transformed_values_np.reshape(df.shape)

        result = pd.DataFrame(transformed_values_np, columns=self.names)
        return result
