__doc__ = """
    This module provides class DefaultRepeater inherited from abstract class Repeater (repeater_abs module).
    Purpose of this repeater - check, using 'provided history', if specific 'provided point' 
    have been measured 'provided number of iterations'."""

from repeater.repeater_abs import Repeater


class DefaultRepeater(Repeater):

    def __init__(self, *args, **kwargs):

        # Initiating parent class and transferring WSClient in *args and other params in **kwargs
        super().__init__(*args, **kwargs)
    
    def decision_function(self, experiment, current_configuration, **configuration):
        """
        Return False while number of measurements less than max_tasks_per_configuration (inherited from abstract class).
        In other case - compute result as average between all experiments for one specific configuration.
        :param experiment: the instance of Experiment class
        :param current_configuration: a configuration under evaluation
                                    shape - list, e.g. ``[1200, 32]``
        :return: result or False
        """

        # Getting all results from experiment;
        # configuration_results is a list of lists of numbers: [exp1, exp2...], where exp1 = [123.1, 123.4, ...]

        configuration_object = experiment.get(current_configuration)
        configuration_results = []
        average_result = []
        if configuration_object:
            configuration_results = experiment.get(current_configuration).get_tasks()
            average_result = experiment.get(current_configuration).get_average_result()

        if len(configuration_results) < self.max_tasks_per_configuration:
            return False
        else:
            return average_result

