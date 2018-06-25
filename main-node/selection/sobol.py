__doc__ = """
Module to read data from files. Each function = 1 file type. 
"""

import sobol_seq
import numpy

class SobolSequence():

    def __init__(self, dimensionality, data):
        """
        Creates SobolSequence instance that stores information about number of generated poitns
        :param dimensionality: - number of different parameters in greed.

        """
        self.dimensionality = dimensionality
        self.data = data
        self.numOfGeneratedPoints = 0

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

        result = []
        # In loop below this distribution imposed to real parameter values list.
        for parameter_index, parameterValue in enumerate(point):
            result.append(self.data[parameter_index][round(len(self.data[parameter_index]) * float(parameterValue) - 1 )])

        return result

    def merge_data_with_selection_algorithm(self, sobol_seq=None, numOfPoints = 'all'):
        """
        Method maps input parameter points to uniformly generated sobol sequence and returns data points.
        Number of parameters should be the same as depth of each point in Sobol sequence.
        It is possible to call method without providing Sobol sequence - it will be generated in runtime.
        :param sobol_seq: data points
        :param numOfPoints: 'all' - all parameters will be mapped to sobol distribution function, or int
        :return: List with uniformly distributed parameters across parameter space.
        """

        if type(sobol_seq) is numpy.ndarray:
            if len(self.data) != len(sobol_seq[0]):
                print("Warning! Number of provided parameters does not match with size of Sobol sequence. Generating own Sobol sequence based on provided parameters.")
                sobol_seq = None

        # The below 'if' case generates sobol sequence
        if not sobol_seq or type(sobol_seq) is not numpy.ndarray:

            if numOfPoints == 'all':
                numOfPoints = 1
                for parameter in self.data:
                    numOfPoints *= len(parameter)

            sobol_seq = self.__generate_sobol_seq(numOfPoints)

        # Following loop apply Sobol grid to given parameter grid, e.g.:
        # for Sobol array(
        #  [[ 0.5  ,  0.5  ],
        #   [ 0.75 ,  0.25 ],
        #   [ 0.25 ,  0.75 ],
        #   [ 0.375,  0.375],
        #   [ 0.875,  0.875]])
        #
        # And params = [
        # [1, 2, 4, 8, 16, 32],
        # [1200.0, 1300.0, 1400.0, 1600.0, 1700.0, 1800.0, 1900.0, 2000.0, 2200.0, 2300.0, 2400.0, 2500.0, 2700.0, 2800.0,
        #   2900.0, 2901.0]
        #               ]
        # We will have output like:
        # [[3.0, 8.0],
        #  [4.5, 4.0],
        #  [1.5, 12.0],
        #  [2.25, 6.0],
        #  [5.25, 14.0]]
        result = []
        for point in sobol_seq:
            tmp_res = []
            for parameter_index, parameterValue in enumerate(point):
                tmp_res.append(self.data[parameter_index][round(len(self.data[parameter_index]) * float(parameterValue) - 1 )])
            result.append(tmp_res)
        return result