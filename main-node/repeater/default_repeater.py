__doc__ = """
    This module provides class DefaultRepeater inherited from abstract class Repeater (repeater_abs module).
    Purpose of this repeater - check, using 'provided history', if specific 'provided point' 
    have been measured 'provided number of iterations'."""

from repeater.history import History
from repeater.repeater_abs import Repeater


class DefaultRepeater(Repeater):
    
    def decision_function(self, history, point, **configuration):
        """
        Return False while number of measurements less than max_repeats_of_experiment (inherited from abstract class).
        In other case - compute result as average between all experiments.
        :param history: history class object that stores all experiments results
        :param point: concrete experiment configuration that is evaluating
        :return: result or False
        """

        # Getting all results from history;
        # all experiments is a list of lists of numbers: [exp1, exp2...], where exp1 = [123.1, 123.4, ...]
        all_experiments = history.get(point)
        if len(all_experiments) < self.max_repeats_of_experiment:
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
