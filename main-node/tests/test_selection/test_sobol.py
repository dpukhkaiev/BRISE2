from selection.sobol import SobolSequence
from itertools import product
import numpy


SEARCH_SPACE = [[1, 2, 4, 8, 16, 32],
                [1200.0, 1300.0, 1400.0, 1600.0, 1700.0, 1800.0, 1900.0, 2000.0, 2200.0, 2300.0, 2400.0, 2500.0,
                 2700.0, 2800.0, 2900.0, 2901.0]]


def test_default_empty_search_space():
    search_space = []
    sobol_sequence = SobolSequence(selection_algorithm_config={}, search_space=search_space)

    assert sobol_sequence.dimensionality == len(search_space)
    assert sobol_sequence.search_space == search_space
    assert sobol_sequence.numOfGeneratedPoints == 0
    assert sobol_sequence.returned_points == []
    assert sobol_sequence.hypercube_coordinates == []
    assert sobol_sequence.hypercube == [()]


def test_default():
    sobol_sequence = SobolSequence(selection_algorithm_config={}, search_space=SEARCH_SPACE)

    assert sobol_sequence.dimensionality == len(SEARCH_SPACE)
    assert sobol_sequence.search_space == SEARCH_SPACE
    assert sobol_sequence.numOfGeneratedPoints == 0
    assert sobol_sequence.returned_points == []

    threads_len = len(SEARCH_SPACE[0])
    frequency_len = len(SEARCH_SPACE[1])
    hypercube_coordinates_expected = [[float(x) for x in range(threads_len)],
                                      [float(x) for x in range(frequency_len)]]
    assert sobol_sequence.hypercube_coordinates == hypercube_coordinates_expected

    hypercube_expected = list(product(*hypercube_coordinates_expected))
    assert sobol_sequence.hypercube == hypercube_expected


# TODO - Error in the comparison: "sequence == sequence_expected"
def test_default_generate_sobol_seq():
    sobol_sequence = SobolSequence(selection_algorithm_config=[], search_space=SEARCH_SPACE)

    sequence = sobol_sequence._SobolSequence__generate_sobol_seq()  # default: number_of_data_points=1, skip=0
    sequence_expected = numpy.array([[0.5, 0.5]])
    # ValueError: The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()
    # assert sequence == sequence_expected
    assert sobol_sequence.numOfGeneratedPoints == 1


# def test_get_next_point():
#     sobol_sequence = SobolSequence(selection_algorithm_config={}, search_space=SEARCH_SPACE)


