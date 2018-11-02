__doc__ = """
    This module provides class DefaultRepeater inherited from abstract class Repeater (repeater_abs module).
    Purpose of this repeater - check, using 'provided history', if specific 'provided point' 
    have been measured 'provided number of iterations'."""

from repeater.repeater_abs import Repeater


class DefaultRepeater(Repeater):

    def __init__(self, *args, **kwargs):

        # Initiating parent class and transferring WSClient in *args and other params in **kwargs
        super().__init__(*args, **kwargs)
    
    def decision_function(self, point, **configuration):
        """
        Return False while number of measurements less than max_repeats_of_experiment (inherited from abstract class).
        In other case - compute result as average between all experiments.
        :param point: concrete experiment configuration that is evaluating
                      shape - tuple, e.g. ``(1200, 32)``
        :return: result or False
        """

        # Getting all results from history;
        # all experiments is a list of lists of numbers: [exp1, exp2...], where exp1 = [123.1, 123.4, ...]
        all_experiments = self.history.get(point)
        if len(all_experiments) < self.max_repeats_of_experiment:
            return False
        else:
            # Summing all results
            result = self.calculate_configs_average(all_experiments)
            return result
