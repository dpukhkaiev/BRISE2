__doc__ = """
    This module provides class DefaultRepeater inherited from abstract class Repeater (repeater_abs module).
    Purpose of this repeater - check, if Configuration measurements are finished (obtained needed number of tasks)."""


class DefaultJudge:
    """
    Repeats each Configuration fixed number of times, no evaluation performed.
    """
    def __init__(self, repeater_configuration: dict):
        """
        :param repeater_configuration: RepeaterConfiguration part of experiment description
        """
        self.max_tasks_per_configuration = repeater_configuration["MaxTasksPerConfiguration"]

    def verdict(self, current_configuration, **params):
        """
        Return False while number of measurements less than max_tasks_per_configuration.
        In other case - compute result as average between all experiments for one specific configuration.
        :param current_configuration: a configuration under evaluation
                                    shape - list, e.g. ``[1200, 32]``
        :return: result or False
        """

        # Getting all results from experiment;
        # configuration_results is a list of lists of numbers: [exp1, exp2...], where exp1 = [123.1, 123.4, ...]

        configuration_results = []
        average_result = []
        if current_configuration:
            configuration_results = current_configuration.get_tasks()
            average_result = current_configuration.get_average_result()

        if len(configuration_results) < self.max_tasks_per_configuration:
            # TODO: Predict number of tasks
            # return abs(self.max_tasks_per_configuraiton - len(configuration_results))
            return False
        else:
            return average_result
