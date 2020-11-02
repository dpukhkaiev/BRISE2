__doc__ = """
    This module provides class QuantityBasedType inherited from abstract class Repeater (repeater.py).
    Purpose of this repeater - check, if Configuration measurements are finished (obtained needed number of tasks)."""
from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from repeater.repeater import Repeater


class QuantityBasedType(Repeater):
    """
    Repeats each Configuration fixed number of times, no evaluation performed.
    """
    def __init__(self, experiment: Experiment, repeater_configuration: dict):
        """
        :
        :param repeater_configuration: RepeaterConfiguration part of experiment description
        """
        super().__init__(experiment)
        self.max_tasks_per_configuration = repeater_configuration["Parameters"]["MaxTasksPerConfiguration"]

    def evaluate(self, current_configuration: Configuration, experiment: Experiment):
        """
        Return max_tasks_per_configuration to measure default Configuration or 0.
        :param current_configuration: instance of Configuration class.
        :param experiment: instance of 'experiment' required by the abstract class. Not used in this strategy.
        :return: max_tasks_per_configuration or 0
        """

        if len(current_configuration.get_tasks()) < self.max_tasks_per_configuration:
            return self.max_tasks_per_configuration - len(current_configuration.get_tasks())
        else:
            return 0
