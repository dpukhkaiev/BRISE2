__doc__ = """
Describes logic of selection algorithm based on Sobol sequences in Sobol space."""

import sobol_seq
import numpy
from selection.selection_algorithm_abs import SelectionAlgorithm
from scipy.spatial.distance import euclidean
from itertools import product

class SobolSequence(SelectionAlgorithm):

    def __init__(self, selection_algorithm_config, search_space):
        """
        Creates SobolSequence instance that stores information about number of generated points
        :param selection_algorithm_config: Dict with configuration of selection algorithm.
        :param search_space: list of dimensions that describes a

        """
        # TODO: Selection algorithm needs to know measured points by regression model

        self.dimensionality = len(search_space)
        self.search_space = search_space
        self.numOfGeneratedPoints = 0
        self.returned_points = []   # Storing previously returned points
        self.hypercube_coordinates = []

        # Need to use floating numbers of indexes for searching distances between target point and other points in hypercube
        for dimension in search_space:
            dim_indexes = [float(x) for x in range(len(dimension))]
            self.hypercube_coordinates.append(dim_indexes)

        # Building hypercube
        self.hypercube = list(product(*self.hypercube_coordinates))

    def __generate_sobol_seq(self, number_of_data_points=1, skip=0):
        """
            Generates sobol sequence of uniformly distributed data points in N dimensional space.
            :param number_of_data_points: int - number of points that needed to be generated in this iteration
            :param skip: int - number of points to skip from the beginning of sequence, because sobol_seq.i4_sobol_generate stateless.
            :return: sobol sequence as numpy array.
        """

        sequence = sobol_seq.i4_sobol_generate(self.dimensionality, skip + number_of_data_points)[skip:]
        self.numOfGeneratedPoints += number_of_data_points
        return sequence

    def get_next_point(self):
        """
        Will return next data point from initiated Sobol sequence imposed to the search space.
        :return:
        """
        # Used to cut out previously generated points - by this counter sobol sequence object knows number of previously
        # returned points and skips them.
        skip = self.numOfGeneratedPoints

        # Getting next point from sobol sequence.
        point = self.__generate_sobol_seq(skip=skip)[0]

        # Imposed this point to hypercube dimension sizes.
        point = [len(self.hypercube_coordinates[dimension_index]) * dimension_value for dimension_index, dimension_value in enumerate(point)]

        # Calculate dictionary (keys - distance, values - point) with distances to self.numOfGeneratedPoints
        # nearest points in search space from this point.
        #
        # self.numOfGeneratedPoints, because in the worst case we will
        # skip(because they was previously returned) this number of points

        distances_dict = {}
        for hypercube_point in self.hypercube:
            if len(distances_dict) < self.numOfGeneratedPoints:
                distances_dict[euclidean(point, hypercube_point)] = hypercube_point
            elif len(distances_dict) == self.numOfGeneratedPoints:
                distances = list(distances_dict.keys())
                distances.sort()
                del(distances_dict[distances.pop()])
                distances_dict[euclidean(point, hypercube_point)] = hypercube_point

        # Picking existing configuration point from hypercube by the smallest distance if it was not previously picked.
        distances = list(distances_dict.keys())
        distances.sort()
        for current_distance in distances:
            if distances_dict[current_distance] not in self.returned_points:
                point = distances_dict[current_distance]
                self.returned_points.append(point)
                break

        # Assign value to this point from search space.
        result_to_return = [self.search_space[int(dimension_index)][int(dimension_value)] for dimension_index, dimension_value in enumerate(point)]
        return result_to_return
