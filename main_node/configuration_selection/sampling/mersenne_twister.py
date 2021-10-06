import random

from configuration_selection.sampling.selection_algorithm_abs import SelectionAlgorithm


class MersenneTwister(SelectionAlgorithm):
    def __init__(self):
        """
        Selection algorithm that uses Mersenne Twister pseudo-random generator. <https://docs.python.org/3/library/random.html>
        """
        super().__init__()

    def get_value(self, dimensionality: int, configuration_number: int, dimension: int) -> float:
        """
        Return the random floating point number in the range [0.0, 1.0).
        """
        return random.random()
