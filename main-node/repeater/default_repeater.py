__doc__="""
    This module provides class DefaultRepeater inherited from abstract class Repeater (repeater_abs module).
    Purpoce of this repeater - check, using 'provided history', if specific 'provided point' 
    have been measured 'provided number of iterations'."""

from repeater.history import History
from repeater.repeater_abs import Repeater


class DefaultRepeater(Repeater):
    
    def decision_function(self, history, point, iterations=10, **configuration):
        """
        Return False while number of measurements less than provided number of iterations.
        In other case - compute result as avarage between all experiments.

        :param iterations: int, number of times to repeat measurement.
        :return: result or False
        """

        # Getting all results from history;
        # all experiments is a list of lists of numbers: [exp1, exp2...], where exp1 = [123.1, 123.4, ...]
        all_experiments = history.get(point)
        if len(all_experiments) < iterations:
            return False
        else:
            # Summing all results
            result = [0 for x in range(len(all_experiments[0]))]
            for experiment in all_experiments:
                for index, value in enumerate(experiment):
                    result[index] += value

            # Calculating average.
            for index, value in enumerate(result):
                result[index] = eval(self.WSClient.results_data_types[index])(round(value / len(all_experiments), 2))

            return result