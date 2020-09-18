__doc__ = """
    Abstract class for creation of selection algorithm with needed methods and fields for ."""
import logging
from abc import ABC, abstractmethod


class SelectionAlgorithm(ABC):

    def __init__(self):

        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def get_value(self, dimensionality: int, configuration_number: int, dimension: int): 
        """
        An abstract selection method.
        Each selection algorithm should return float in range (0...1).
        """
        pass
