"""
The per-Configuration budget the RepetitionManager honours for the Racing layer.

BudgetAwareRepeater decorates whichever Instance the Experiment declares, so the
Instance itself stays unaware of rungs: it keeps its own task target and is only
overruled for a Configuration that carries a budget of its own.
"""
import logging
import unittest
from unittest.mock import patch

from core_entities.configuration import Configuration

logging.disable(logging.CRITICAL)

QUANTITY_BASED_DESCRIPTION = {
    "RepetitionManager": {
        "MaxFailedTasksPerConfiguration": 1,
        "Instance": {"QuantityBased": {"MaxTasksPerConfiguration": 3, "Type": "quantity_based"}}
    }
}

REPETITIONS_DESCRIPTION = {
    "RepetitionManager": {
        **QUANTITY_BASED_DESCRIPTION["RepetitionManager"],
        "BudgetSchedule": {"Eta": 3, "MinBudget": 1, "MaxBudget": 9, "BudgetType": "repetitions"}
    }
}

TASK_TIME_DESCRIPTION = {
    "RepetitionManager": {
        **QUANTITY_BASED_DESCRIPTION["RepetitionManager"],
        "BudgetSchedule": {"Eta": 3, "MinBudget": 1, "MaxBudget": 9, "BudgetType": "task_time"}
    }
}


def _configuration_with_tasks(task_count, task_budget=None):
    Configuration.set_task_config({"Objectives": {"objective": {"Name": "objective"}}})
    configuration = Configuration({"x": 1}, Configuration.Type.PREDICTED, "experiment")
    configuration._tasks = {str(i): {} for i in range(task_count)}
    configuration.task_budget = task_budget
    return configuration


def _budget_aware(description, wrapped=None):
    with patch("repeater.repeater.MongoDB"):
        from repeater.budget_aware import BudgetAwareRepeater
        from repeater.quantity_based import QuantityBasedType
        if wrapped is None:
            wrapped = QuantityBasedType(description, "experiment")
        return BudgetAwareRepeater(wrapped, description, "experiment")


class TestRepetitionBudget(unittest.TestCase):
    """A rung counted in repetitions overrides the Instance's task target."""

    def setUp(self):
        self.repeater = _budget_aware(REPETITIONS_DESCRIPTION)

    def test_without_a_budget_the_instance_decides(self):
        self.assertEqual(self.repeater.evaluate(_configuration_with_tasks(0)), 3)
        self.assertEqual(self.repeater.evaluate(_configuration_with_tasks(3)), 0)

    def test_promotion_requests_only_the_delta(self):
        # Tasks accumulate, so a rung-2 survivor reuses its 3 rung-1 measurements.
        self.assertEqual(self.repeater.evaluate(_configuration_with_tasks(3, task_budget=9)), 6)

    def test_reached_budget_needs_no_task(self):
        self.assertEqual(self.repeater.evaluate(_configuration_with_tasks(9, task_budget=9)), 0)

    def test_budget_below_the_instance_target_still_wins(self):
        # Rung 0 measures less than MaxTasksPerConfiguration, not more.
        self.assertEqual(self.repeater.evaluate(_configuration_with_tasks(0, task_budget=1)), 1)
        self.assertEqual(self.repeater.evaluate(_configuration_with_tasks(1, task_budget=1)), 0)


class TestTaskTimeBudget(unittest.TestCase):
    """
    With a task_time budget the rung goes INTO the Task, so the number of Tasks
    stays whatever the Instance asks for no matter which rung a Configuration is on.
    """

    def setUp(self):
        self.repeater = _budget_aware(TASK_TIME_DESCRIPTION)

    def test_high_rung_does_not_request_repetitions(self):
        self.assertEqual(self.repeater.evaluate(_configuration_with_tasks(0, task_budget=9)), 3)
        self.assertEqual(self.repeater.evaluate(_configuration_with_tasks(3, task_budget=9)), 0)

    def test_promoted_configuration_is_measured_afresh(self):
        # main.py resets the Tasks of a promoted survivor, so it asks for the
        # Instance's count again - now at the higher Task budget.
        self.assertEqual(self.repeater.evaluate(_configuration_with_tasks(0, task_budget=3)), 3)


class TestDecoratesAnyInstance(unittest.TestCase):
    """The decorator knows nothing about which Instance it wraps."""

    class _StubRepeater:
        def __init__(self):
            self.calls = []

        def evaluate(self, current_configuration):
            self.calls.append(current_configuration)
            return 42

    def test_delegates_when_there_is_no_budget(self):
        stub = self._StubRepeater()
        repeater = _budget_aware(REPETITIONS_DESCRIPTION, wrapped=stub)
        self.assertEqual(repeater.evaluate(_configuration_with_tasks(0)), 42)
        self.assertEqual(len(stub.calls), 1)

    def test_overrides_the_instance_when_a_budget_is_carried(self):
        stub = self._StubRepeater()
        repeater = _budget_aware(REPETITIONS_DESCRIPTION, wrapped=stub)
        self.assertEqual(repeater.evaluate(_configuration_with_tasks(2, task_budget=9)), 7)
        self.assertEqual(stub.calls, [])


class TestSelectorWiring(unittest.TestCase):
    """Only a declared BudgetSchedule puts the decorator in the chain."""

    def _repeater_for(self, description):
        import os
        from unittest.mock import MagicMock
        os.environ["TEST_MODE"] = "UNIT_TEST"
        from repeater.repeater_selector import RepeaterOrchestration
        orchestrator = RepeaterOrchestration.__new__(RepeaterOrchestration)
        orchestrator.experiment_description = description
        orchestrator.experiment_id = "experiment"
        orchestrator.experiment = MagicMock()
        with patch("repeater.repeater.MongoDB"):
            return orchestrator.get_repeater(is_default_configuration=True)

    def test_ladder_present_wraps(self):
        from repeater.budget_aware import BudgetAwareRepeater
        self.assertIsInstance(self._repeater_for(REPETITIONS_DESCRIPTION), BudgetAwareRepeater)

    def test_no_ladder_leaves_the_instance_bare(self):
        from repeater.budget_aware import BudgetAwareRepeater
        from repeater.quantity_based import QuantityBasedType
        repeater = self._repeater_for(QUANTITY_BASED_DESCRIPTION)
        self.assertNotIsInstance(repeater, BudgetAwareRepeater)
        self.assertIsInstance(repeater, QuantityBasedType)


if __name__ == "__main__":
    unittest.main()
