__doc__ = """
Module to read data from files. Each function = 1 file type. 
"""

import sobol_seq
import numpy
from selection.selection_algorithm_abs import SelectionAlgorithm
from scipy.spatial.distance import euclidean
from itertools import product

class SobolSequence(SelectionAlgorithm):

    def __init__(self, data):
        """
        Creates SobolSequence instance that stores information about number of generated poitns
        :param data: list of dimensions that describes a

        """
        # TODO: Selection algorithm needs to know measured points by regression model

        self.dimensionality = len(data)
        self.data = data
        self.numOfGeneratedPoints = 0
        self.returned_points = []   # Storing previously returned points
        self.hypercube_coordinates = []

        # Need to use floating numbers of indexes for searching distances between target point and other points in hypercube
        for dimmension in data:
            dimm_indexes = [float(x) for x in range(len(dimmension))]
            self.hypercube_coordinates.append(dimm_indexes)

        # Building hypercube
        self.hypercube = list(product(*self.hypercube_coordinates))


    def __generate_sobol_seq(self, number_of_data_points=1, skip = 0):
        """
            Generates sobol sequence of uniformly distributed data points in N dimensional space.
            :param number_of_data_points: int - number of points that needed to be generated in this iteration
            :return: sobol sequence as numpy array.
        """

        sequence = sobol_seq.i4_sobol_generate(self.dimensionality, skip + number_of_data_points)[skip:]
        self.numOfGeneratedPoints += number_of_data_points

        return sequence

    def get_next_point(self):
        """
        Will return next data point from initiated Sobol sequence.
        :return:
        """
        # Cut out previously generated points.
        skip = self.numOfGeneratedPoints

        # Point is a list with floats uniformly distributed between 0 and 1 for all parameters [paramA, paramB..]
        point = self.__generate_sobol_seq(skip=skip)[0]

        # Putting this point to hypercube
        point = [len(self.hypercube_coordinates[dimension_index]) * dimension_value for dimension_index, dimension_value in enumerate(point)]

        # Calculate dictionary with distances to all other points in search space from this point
        # Keys - distance, values - point
        distances_dict = {}
        for hypercube_point in self.hypercube:
            distances_dict[euclidean(point, hypercube_point)] = hypercube_point

        # Picking existing configuration point from hypercube by the smallest distance if it was not previously picked.
        distances = list(distances_dict.keys())
        distances.sort()
        for current_distance in distances:
            if distances_dict[current_distance] not in self.returned_points:
                point = distances_dict[current_distance]
                self.returned_points.append(point)
                break
            # Only for debug, need to remove it.
            else:
                print("Woops, it was picked, taking next one!")

        # Retrieve configuration from the task
        result_to_return = [self.data[int(dimension_index)][int(dimension_value)] for dimension_index, dimension_value in enumerate(point)]



        """
        result_to_return = []
        # In loop below this distribution imposed to real parameter values list.
        for parameter_index, parameterValue in enumerate(point):
            result_to_return.append(self.search_space[parameter_index][round(len(self.search_space[parameter_index]) * float(parameterValue) - 1 )])
        """
        return result_to_return
