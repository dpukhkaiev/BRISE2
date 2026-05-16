__doc__ = """
    This module provides class QuantityBasedType inherited from abstract class Repeater (repeater.py).
    Purpose of this repeater - check, if Configuration measurements are finished (obtained needed number of tasks)."""
from core_entities.configuration import Configuration
from repeater.repeater import Repeater


class QuantityBasedType(Repeater):
    """
    Repeats each Configuration fixed number of times, no evaluation performed.
    """
    def __init__(self, experiment_description: dict, experiment_id: str, experiment=None):
        """
        :param experiment_description: experiment description in json format
        :param experiment_id: ID of experiment, processed by this module
        :param experiment: Experiment class instance, (!)used only in tests
        """
        super().__init__(experiment_description, experiment_id)
        feature_name = list(self.repeater_configuration["Instance"].keys())[0]
        self.max_tasks_per_configuration = self.repeater_configuration["Instance"][feature_name]["MaxTasksPerConfiguration"]

    def evaluate(self, current_configuration: Configuration):
        """
        Return max_tasks_per_configuration to measure default Configuration or 0.
        :param current_configuration: instance of Configuration class.
        :return: max_tasks_per_configuration or 0
        """

        if len(current_configuration.get_tasks()) < self.max_tasks_per_configuration:
            return self.max_tasks_per_configuration - len(current_configuration.get_tasks())
        else:
            return 0
