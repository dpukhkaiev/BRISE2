__doc__ = """
    This module provides class BudgetAwareRepeater, a decorator around a concrete
    Repeater (repeater.py) that lets a Configuration carry a measurement budget of
    its own - the rung budget assigned by the Racing layer."""
from core_entities.configuration import Configuration
from repeater.budget_type import is_task_time_budget
from repeater.repeater import Repeater


class BudgetAwareRepeater(Repeater):
    """
    Overrides the wrapped Repeater's task target with the Configuration's own
    budget, whenever RepetitionManager.BudgetSchedule declares one.

    Tasks accumulate on a Configuration, so a promotion to a higher rung only
    requests the delta and reuses every measurement already taken.

    A task_time budget goes into the Task instead of multiplying it
    (WSClient._task_budget), so there the rung changes what a Task measures, not
    how many are needed, and the wrapped Repeater decides alone.
    """

    def __init__(self, wrapped: Repeater, experiment_description: dict, experiment_id: str):
        super().__init__(experiment_description, experiment_id)
        self.wrapped = wrapped
        self.budget_scales_task = is_task_time_budget(experiment_description)

    def evaluate(self, current_configuration: Configuration) -> int:
        """
        :param current_configuration: instance of Configuration class.
        :return: number of tasks still to perform.
        """
        if self.budget_scales_task or not current_configuration.task_budget:
            return self.wrapped.evaluate(current_configuration)
        return max(0, current_configuration.task_budget - len(current_configuration.get_tasks()))
