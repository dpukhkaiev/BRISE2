__doc__ = """
    Describes logic of selection algorithm based on Sobol sequences in Sobol space."""

import sobol_seq
from configuration_selection.sampling.selection_algorithm_abs import SelectionAlgorithm


class SobolSequence(SelectionAlgorithm):
    def __init__(self):
        """
        Selection algorithm that uses Sobol Sequence generator. <https://github.com/naught101/sobol_seq#usage>
        """
        super().__init__()

    def get_value(self, dimensionality: int, configuration_number: int, dimension: int) -> float:
        """
            Generates a next sobol vector in the current search space.
            :return: value from sobol vector which represents current dimension.
        """
        vector, _ = sobol_seq.i4_sobol(dimensionality, configuration_number)
        return vector[dimension]
