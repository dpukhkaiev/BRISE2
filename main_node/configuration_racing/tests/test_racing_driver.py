"""
The message-bus half of Racing: MainThread._drive_racing.

The strategy is transport-free by design, so everything that turns a decision
into a message - which exchange, what the promoted copy looks like, when the
rung safety net is armed - lives in the core and is only covered here.
"""
import json
import logging
import os
import unittest
from unittest.mock import MagicMock, patch

os.environ["TEST_MODE"] = "UNIT_TEST"

from core_entities.configuration import Configuration
from configuration_racing.racing_abs import RacingDecision
from main import MainThread

logging.disable(logging.CRITICAL)

TASK_CONFIGURATION = {
    "TaskName": "test",
    "Objectives": {"Y1": {"Name": "Y1", "Minimization": True}}
}
REPETITIONS_DESCRIPTION = {
    "Context": {"TaskConfiguration": TASK_CONFIGURATION},
    "RepetitionManager": {"BudgetSchedule": {"BudgetType": "repetitions"}}
}
TASK_TIME_DESCRIPTION = {
    "Context": {"TaskConfiguration": TASK_CONFIGURATION},
    "RepetitionManager": {"BudgetSchedule": {"BudgetType": "task_time"}}
}


def _configuration(objective_value=0.5, task_count=3):
    Configuration.set_task_config(TASK_CONFIGURATION)
    configuration = Configuration({"x": 1}, Configuration.Type.PREDICTED, "experiment")
    configuration._tasks = {str(i): {} for i in range(task_count)}
    configuration.results = {"Y1": objective_value}
    configuration.status = {'enabled': True, 'evaluated': True, 'measured': True}
    return configuration


class _DriverTestCase(unittest.TestCase):

    description = REPETITIONS_DESCRIPTION
    rung_timeout = None

    def setUp(self):
        self.main = MainThread.__new__(MainThread)
        self.main._is_interrupted = False
        self.main._rung_timer = None
        self.main.logger = MagicMock()
        self.main.experiment = MagicMock()
        self.main.experiment.description = self.description
        self.main.experiment.unique_id = "experiment-1"
        self.main.experiment.get_objectives_minimization.return_value = [True]
        self.main.racing = MagicMock()
        self.main.racing.rung_timeout_seconds = self.rung_timeout

        publish_patcher = patch("main.publish")
        self.publish = publish_patcher.start()
        self.addCleanup(publish_patcher.stop)

    def published_to(self, exchange):
        return [call for call in self.publish.call_args_list
                if call.kwargs.get("exchange") == exchange]


class TestPromote(_DriverTestCase):

    def test_promoted_copy_is_redispatched_for_measurement(self):
        survivor = _configuration(task_count=3)
        self.main._drive_racing(
            RacingDecision.promote([survivor], budget=9, token=1))

        published = self.published_to('measure_new_configuration_exchange')
        self.assertEqual(len(published), 1)
        promoted = Configuration.from_json(
            json.loads(published[0].kwargs["body"])["configuration"])
        self.assertEqual(promoted.task_budget, 9)
        self.assertEqual(promoted.rung_token, 1)
        self.assertFalse(promoted.status['evaluated'])
        self.assertFalse(promoted.status['measured'])

    def test_original_is_left_measured(self):
        survivor = _configuration()
        self.main._drive_racing(
            RacingDecision.promote([survivor], budget=9, token=1))
        self.assertTrue(survivor.status['measured'])
        self.assertIsNone(survivor.task_budget)

    def test_repetition_budget_keeps_the_tasks_already_taken(self):
        # The repeater then only asks for the delta up to the new rung budget.
        self.main._drive_racing(
            RacingDecision.promote([_configuration(task_count=3)], budget=9, token=1))
        promoted = Configuration.from_json(json.loads(
            self.published_to('measure_new_configuration_exchange')[0].kwargs["body"])["configuration"])
        self.assertEqual(len(promoted.get_tasks()), 3)

    def test_every_survivor_is_dispatched(self):
        survivors = [_configuration(0.1), _configuration(0.2), _configuration(0.3)]
        self.main._drive_racing(
            RacingDecision.promote(survivors, budget=3, token=1))
        self.assertEqual(len(self.published_to('measure_new_configuration_exchange')), 3)


class TestPromoteWithTaskTimeBudget(_DriverTestCase):

    description = TASK_TIME_DESCRIPTION

    def test_survivor_is_measured_afresh(self):
        """
        A task_time rung raises the fidelity of one Task, so the cheaper Tasks
        measured a different quantity and must not be averaged into the new one.
        """
        self.main._drive_racing(
            RacingDecision.promote([_configuration(task_count=3)], budget=9, token=1))
        promoted = Configuration.from_json(json.loads(
            self.published_to('measure_new_configuration_exchange')[0].kwargs["body"])["configuration"])
        self.assertEqual(len(promoted.get_tasks()), 0)
        self.assertEqual(promoted.task_budget, 9)


class TestNewBracketAndStop(_DriverTestCase):

    def test_new_bracket_requests_the_whole_rung_zero_wave(self):
        self.main._drive_racing(
            RacingDecision.new_bracket(number_of_configurations=9, budget=1, token=4))

        published = self.published_to('get_new_configuration_exchange')
        self.assertEqual(len(published), 1)
        body = json.loads(published[0].kwargs["body"])
        self.assertEqual(body["worker_capacity"], 9)
        self.assertEqual(body["task_budget"], 1)
        # Selection echoes the token back so a stale report can be recognised.
        self.assertEqual(body["wave_token"], 4)

    def test_stop_terminates_the_experiment(self):
        self.main._drive_racing(RacingDecision.stop())
        self.assertEqual(len(self.published_to('stop_experiment_exchange')), 1)

    def test_wait_publishes_nothing(self):
        self.main._drive_racing(RacingDecision.wait())
        self.publish.assert_not_called()


class TestRungTimer(_DriverTestCase):

    rung_timeout = 30.0

    def test_no_timer_without_a_configured_timeout(self):
        self.main.racing.rung_timeout_seconds = None
        self.main._drive_racing(
            RacingDecision.new_bracket(number_of_configurations=9, budget=1, token=0))
        self.assertIsNone(self.main._rung_timer)

    def test_timer_is_armed_for_the_rung_a_decision_opens(self):
        self.main._drive_racing(
            RacingDecision.new_bracket(number_of_configurations=9, budget=1, token=0))
        self.assertIsNotNone(self.main._rung_timer)
        self.assertEqual(self.main._rung_timer.args, (0,))
        self.assertEqual(self.main._rung_timer.interval, 30.0)
        self.main._cancel_rung_timer()

    def test_wait_leaves_the_running_timer_alone(self):
        self.main._drive_racing(
            RacingDecision.new_bracket(number_of_configurations=9, budget=1, token=0))
        armed = self.main._rung_timer
        self.main._drive_racing(RacingDecision.wait())
        self.assertIs(self.main._rung_timer, armed)
        self.main._cancel_rung_timer()

    def test_closing_decision_replaces_the_timer(self):
        self.main._drive_racing(
            RacingDecision.new_bracket(number_of_configurations=9, budget=1, token=0))
        first = self.main._rung_timer
        self.main._drive_racing(
            RacingDecision.promote([_configuration()], budget=3, token=1))
        self.assertIsNot(self.main._rung_timer, first)
        self.assertEqual(self.main._rung_timer.args, (1,))
        # cancel() sets the Timer's finished event at once; the thread itself may
        # still be winding down, so is_alive() would be flaky here.
        self.assertTrue(first.finished.is_set())
        self.main._cancel_rung_timer()

    def test_stop_disarms_the_timer(self):
        self.main._drive_racing(
            RacingDecision.new_bracket(number_of_configurations=9, budget=1, token=0))
        self.main._drive_racing(RacingDecision.stop())
        self.assertIsNone(self.main._rung_timer)


class TestWaveDispatchHook(_DriverTestCase):

    def setUp(self):
        super().setUp()
        import threading
        self.main.conf_lock = threading.Lock()

    def test_report_is_forwarded_to_the_strategy(self):
        self.main.racing.on_wave_dispatched.return_value = RacingDecision.wait()
        self.main._on_wave_dispatched(6, 2)
        self.main.racing.on_wave_dispatched.assert_called_once_with(6, [True], 2)

    def test_resulting_decision_is_driven(self):
        self.main.racing.on_wave_dispatched.return_value = \
            RacingDecision.promote([_configuration()], budget=3, token=1)
        self.main._on_wave_dispatched(2, 0)
        self.assertEqual(len(self.published_to('measure_new_configuration_exchange')), 1)

    def test_interrupted_experiment_ignores_the_report(self):
        self.main._is_interrupted = True
        self.main._on_wave_dispatched(6, 2)
        self.main.racing.on_wave_dispatched.assert_not_called()
        self.publish.assert_not_called()

    def test_timeout_is_forwarded_and_driven(self):
        self.main.racing.on_rung_timeout.return_value = RacingDecision.stop()
        self.main._on_rung_timeout(3)
        self.main.racing.on_rung_timeout.assert_called_once_with([True], 3)
        self.assertEqual(len(self.published_to('stop_experiment_exchange')), 1)


if __name__ == "__main__":
    unittest.main()
