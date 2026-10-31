"""
What a rung budget buys: repetitions of a Task, or budget inside one Task.

Covers the resolution of BudgetType from an Experiment Description, the scaling
of a Scenario for one rung, and the Task description the WSClient composes from
both - the single place where a rung reaches a Worker.
"""
import logging
import unittest

from core_entities.configuration import Configuration
from repeater.budget_type import (
    REPETITIONS,
    TASK_TIME,
    budget_schedule,
    budget_type,
    is_task_time_budget,
    scale_scenario_budget
)

logging.disable(logging.CRITICAL)

SCENARIO = {"Problem": "TSP", "Budget": {"Type": "StoppingByTime", "Amount": 30}}


def description(budget_type_value=None, with_ladder=True):
    ladder = {"Eta": 3, "MinBudget": 1, "MaxBudget": 9}
    if budget_type_value:
        ladder["BudgetType"] = budget_type_value
    result = {"Context": {"TaskConfiguration": {"Scenario": SCENARIO, "MaxTimeToRunTask": 60}},
              "RepetitionManager": {"MaxFailedTasksPerConfiguration": 1,
                                    "Instance": {"QuantityBased": {"MaxTasksPerConfiguration": 1,
                                                                   "Type": "quantity_based"}}}}
    if with_ladder:
        result["RepetitionManager"]["BudgetSchedule"] = ladder
    return result


class TestBudgetType(unittest.TestCase):

    def test_repetitions_is_the_default(self):
        self.assertEqual(budget_type(description()), REPETITIONS)
        self.assertEqual(budget_type(description(with_ladder=False)), REPETITIONS)
        self.assertFalse(is_task_time_budget(description()))

    def test_ladder_is_read_from_the_repetition_manager(self):
        self.assertEqual(budget_schedule(description())["MaxBudget"], 9)
        self.assertIsNone(budget_schedule(description(with_ladder=False)))
        self.assertIsNone(budget_schedule({}))

    def test_task_time_is_recognised(self):
        self.assertEqual(budget_type(description(TASK_TIME)), TASK_TIME)
        self.assertTrue(is_task_time_budget(description(TASK_TIME)))


class TestScenarioScaling(unittest.TestCase):

    def test_rung_multiplies_the_declared_amount(self):
        self.assertEqual(scale_scenario_budget(SCENARIO, 3)["Budget"]["Amount"], 90)
        self.assertEqual(scale_scenario_budget(SCENARIO, 9)["Budget"]["Amount"], 270)

    def test_lowest_rung_and_no_budget_stay_untouched(self):
        self.assertEqual(scale_scenario_budget(SCENARIO, 1)["Budget"]["Amount"], 30)
        self.assertEqual(scale_scenario_budget(SCENARIO, None)["Budget"]["Amount"], 30)

    def test_declared_scenario_is_not_mutated(self):
        scale_scenario_budget(SCENARIO, 9)
        self.assertEqual(SCENARIO["Budget"]["Amount"], 30)


class TestTaskDescriptionBudget(unittest.TestCase):
    """WSClient._task_budget: what one Task of a promoted Configuration runs with."""

    def _client(self, budget_scales_task):
        from WorkerServiceClient.WSClient_events import WSClient
        client = WSClient.__new__(WSClient)
        client.logger = logging.getLogger("test")
        client._scenario = SCENARIO
        client._time_for_one_task_running = 60
        client._budget_scales_task = budget_scales_task
        return client

    def _configuration(self, task_budget):
        Configuration.set_task_config({"Objectives": {"objective": {"Name": "objective"}}})
        configuration = Configuration({"x": 1}, Configuration.Type.PREDICTED, "experiment")
        configuration.task_budget = task_budget
        return configuration

    def test_task_time_scales_budget_and_straggler_limit(self):
        client = self._client(budget_scales_task=True)
        scenario, time_for_run = client._task_budget(self._configuration(9))
        self.assertEqual(scenario["Budget"]["Amount"], 270)
        # a 270 s Task must not be terminated after 60 s (worker_service/intro.py:47)
        self.assertEqual(time_for_run, 540)

    def test_repetition_budget_leaves_the_task_alone(self):
        client = self._client(budget_scales_task=False)
        scenario, time_for_run = client._task_budget(self._configuration(9))
        self.assertEqual(scenario["Budget"]["Amount"], 30)
        self.assertEqual(time_for_run, 60)

    def test_default_configuration_without_budget(self):
        client = self._client(budget_scales_task=True)
        scenario, time_for_run = client._task_budget(self._configuration(None))
        self.assertEqual(scenario["Budget"]["Amount"], 30)
        self.assertEqual(time_for_run, 60)

    def test_unlimited_straggler_limit_stays_unlimited(self):
        client = self._client(budget_scales_task=True)
        client._time_for_one_task_running = float("inf")
        _, time_for_run = client._task_budget(self._configuration(9))
        self.assertEqual(time_for_run, float("inf"))


if __name__ == "__main__":
    unittest.main()
