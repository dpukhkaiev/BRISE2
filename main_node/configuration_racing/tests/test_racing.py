import logging
import unittest

from configuration_racing.racing_abs import DecisionKind
from configuration_racing.racing_orchestrator import RacingOrchestrator
from configuration_racing.successive_halving import SuccessiveHalving
from repeater.budget_schedule import BudgetSchedule, HyperbandSchedule

logging.disable(logging.CRITICAL)


class FakeConfiguration:
    """Duck-typed stand-in exercising only what the ranking touches."""

    def __init__(self, objective_value):
        self.results = {"objective": objective_value} if objective_value is not None else {}
        self.task_budget = None
        self.rung_token = None

    def is_better(self, objectives_minimization, other):
        minimize = objectives_minimization[0]
        if minimize:
            return self.results["objective"] < other.results["objective"]
        return self.results["objective"] > other.results["objective"]


def sh_config(eta=3, n=9, min_budget=1, max_budget=9, number_of_brackets=1,
              budget_type="repetitions", rung_timeout=None):
    """
    An Experiment Description declaring a race: the ladder belongs to the
    RepetitionManager, the race control to Racing.
    """
    strategy = {"N": n, "NumberOfBrackets": number_of_brackets, "Type": "successive_halving"}
    if rung_timeout is not None:
        strategy["RungTimeout"] = {"TimeoutInSeconds": rung_timeout}
    return {
        "RepetitionManager": {
            "MaxFailedTasksPerConfiguration": 1,
            "Instance": {"QuantityBased": {"MaxTasksPerConfiguration": 1, "Type": "quantity_based"}},
            "BudgetSchedule": {"Eta": eta, "MinBudget": min_budget, "MaxBudget": max_budget,
                               "BudgetType": budget_type}
        },
        "Racing": {"SuccessiveHalving": strategy}
    }


class TestBudgetSchedule(unittest.TestCase):

    def test_geometric_ladder(self):
        schedule = BudgetSchedule(eta=3, n=9, min_budget=1, max_budget=9)
        self.assertEqual([(r.n_configurations, r.budget) for r in schedule.rungs],
                         [(9, 1), (3, 3), (1, 9)])
        self.assertEqual([schedule.survivors_after(i) for i in range(schedule.number_of_rungs)],
                         [3, 1, 0])

    def test_budget_capped_at_max(self):
        schedule = BudgetSchedule(eta=2, n=8, min_budget=1, max_budget=4)
        self.assertEqual([(r.n_configurations, r.budget) for r in schedule.rungs],
                         [(8, 1), (4, 2), (2, 4)])

    def test_ladder_stops_when_no_survivor(self):
        # max_budget is generous, so the single-survivor rule ends the ladder.
        schedule = BudgetSchedule(eta=3, n=9, min_budget=1, max_budget=1000)
        self.assertEqual(schedule.rungs[-1].n_configurations, 1)

    def test_number_of_rungs_caps_the_ladder(self):
        schedule = BudgetSchedule(eta=3, n=9, min_budget=1, max_budget=9, number_of_rungs=2)
        self.assertEqual([(r.n_configurations, r.budget) for r in schedule.rungs], [(9, 1), (3, 3)])

    def test_invalid_parameters(self):
        with self.assertRaises(ValueError):
            BudgetSchedule(eta=1, n=9, min_budget=1, max_budget=9)
        with self.assertRaises(ValueError):
            BudgetSchedule(eta=3, n=9, min_budget=9, max_budget=1)


class TestHyperbandSchedule(unittest.TestCase):

    @staticmethod
    def _ladders(schedule):
        return [[(r.n_configurations, r.budget) for r in bracket.rungs] for bracket in schedule]

    def test_reproduces_hyperband_paper_example(self):
        # Li et al. (2018), Fig. 1: R = 81, eta = 3 -> n_s = 81, 34, 15, 8, 5.
        schedule = HyperbandSchedule(eta=3, n=81, min_budget=1, max_budget=81, number_of_brackets=5)
        self.assertEqual(schedule.s_max, 4)
        self.assertEqual([bracket.rungs[0].n_configurations for bracket in schedule], [81, 34, 15, 8, 5])
        self.assertEqual([bracket.rungs[0].budget for bracket in schedule], [1, 3, 9, 27, 81])
        self.assertEqual([(r.n_configurations, r.budget) for r in schedule[2].rungs],
                         [(15, 9), (5, 27), (1, 81)])

    def test_brackets_trade_configurations_against_budget(self):
        schedule = HyperbandSchedule(eta=3, n=9, min_budget=1, max_budget=9, number_of_brackets=3)
        self.assertEqual(self._ladders(schedule),
                         [[(9, 1), (3, 3), (1, 9)],
                          [(5, 3), (1, 9)],
                          [(3, 9)]])

    def test_bracket_cycle_repeats(self):
        schedule = HyperbandSchedule(eta=3, n=9, min_budget=1, max_budget=9, number_of_brackets=5)
        self.assertEqual(self._ladders(schedule)[3:], [[(9, 1), (3, 3), (1, 9)], [(5, 3), (1, 9)]])

    def test_n_anchors_the_widest_bracket(self):
        schedule = HyperbandSchedule(eta=3, n=6, min_budget=1, max_budget=9, number_of_brackets=3)
        self.assertEqual(self._ladders(schedule),
                         [[(6, 1), (2, 3)],
                          [(3, 3), (1, 9)],
                          [(2, 9)]])

    def test_non_geometric_budget_range_is_truncated(self):
        schedule = HyperbandSchedule(eta=3, n=9, min_budget=1, max_budget=10, number_of_brackets=1)
        self.assertEqual(self._ladders(schedule), [[(9, 1), (3, 3), (1, 9)]])


class TestRacingOrchestrator(unittest.TestCase):

    def setUp(self):
        self.orchestrator = RacingOrchestrator()

    def test_absent_feature_returns_none(self):
        self.assertIsNone(self.orchestrator.get_racing({}))
        self.assertIsNone(self.orchestrator.get_racing({"Racing": None}))

    def test_selects_successive_halving(self):
        strategy = self.orchestrator.get_racing(sh_config())
        self.assertIsInstance(strategy, SuccessiveHalving)
        self.assertEqual(strategy.number_of_brackets, 1)

    def test_ladder_is_read_from_the_repetition_manager(self):
        strategy = self.orchestrator.get_racing(sh_config(eta=2, min_budget=1, max_budget=8))
        self.assertEqual(strategy.eta, 2)
        self.assertEqual([r.budget for r in strategy.schedule[0].rungs], [1, 2, 4, 8])


class TestSuccessiveHalving(unittest.TestCase):

    minimization = [True]

    def _run_rung(self, controller, objective_values):
        decision = None
        for value in objective_values:
            decision = controller.on_configuration_measured(FakeConfiguration(value), self.minimization)
        return decision

    def test_start_requests_rung_zero_batch(self):
        controller = SuccessiveHalving(sh_config(n=9))
        decision = controller.start()
        self.assertEqual(decision.kind, DecisionKind.NEW_BRACKET)
        self.assertEqual(decision.number_of_configurations, 9)
        self.assertEqual(decision.budget, 1)

    def test_waits_until_rung_is_full(self):
        controller = SuccessiveHalving(sh_config(n=9))
        controller.start()
        for value in range(8):
            self.assertEqual(controller.on_configuration_measured(
                FakeConfiguration(value), self.minimization).kind, DecisionKind.WAIT)

    def test_promotes_only_the_best_survivors(self):
        controller = SuccessiveHalving(sh_config(eta=3, n=9, min_budget=1, max_budget=9))
        controller.start()
        decision = self._run_rung(controller, [5, 3, 8, 1, 7, 2, 9, 4, 6])
        self.assertEqual(decision.kind, DecisionKind.PROMOTE)
        self.assertEqual(decision.budget, 3)
        self.assertEqual(sorted(c.results["objective"] for c in decision.configurations), [1, 2, 3])

    def test_single_bracket_stops_after_last_rung(self):
        controller = SuccessiveHalving(sh_config(eta=3, n=9, number_of_brackets=1))
        controller.start()
        self.assertEqual(self._run_rung(controller, [5, 3, 8, 1, 7, 2, 9, 4, 6]).kind, DecisionKind.PROMOTE)
        self.assertEqual(self._run_rung(controller, [3, 1, 2]).kind, DecisionKind.PROMOTE)
        self.assertEqual(self._run_rung(controller, [1]).kind, DecisionKind.STOP)

    def test_next_bracket_trades_configurations_against_budget(self):
        controller = SuccessiveHalving(sh_config(eta=3, n=9, number_of_brackets=2))
        controller.start()
        self._run_rung(controller, [5, 3, 8, 1, 7, 2, 9, 4, 6])
        self._run_rung(controller, [3, 1, 2])
        new_bracket = self._run_rung(controller, [1])
        self.assertEqual(new_bracket.kind, DecisionKind.NEW_BRACKET)
        self.assertEqual(new_bracket.number_of_configurations, 5)
        self.assertEqual(new_bracket.budget, 3)

    def test_last_bracket_races_without_elimination(self):
        controller = SuccessiveHalving(sh_config(eta=3, n=9, number_of_brackets=3))
        controller.start()
        self._run_rung(controller, [5, 3, 8, 1, 7, 2, 9, 4, 6])
        self._run_rung(controller, [3, 1, 2])
        self._run_rung(controller, [1])
        self._run_rung(controller, [5, 3, 8, 1, 7])
        last_bracket = self._run_rung(controller, [1])
        self.assertEqual(last_bracket.number_of_configurations, 3)
        self.assertEqual(last_bracket.budget, 9)
        self.assertEqual(self._run_rung(controller, [3, 1, 2]).kind, DecisionKind.STOP)

    def test_budgets_follow_the_schedule(self):
        controller = SuccessiveHalving(sh_config(eta=3, n=9, min_budget=2, max_budget=18))
        controller.start()
        self.assertEqual(self._run_rung(controller, [5, 3, 8, 1, 7, 2, 9, 4, 6]).budget, 6)
        self.assertEqual(self._run_rung(controller, [3, 1, 2]).budget, 18)

    def test_configurations_without_results_rank_last(self):
        controller = SuccessiveHalving(sh_config(eta=3, n=9))
        controller.start()
        # three configs have no results; they must not survive over measured ones.
        decision = self._run_rung(controller, [5, 3, None, 1, None, 2, None, 4, 6])
        survivors = [c.results.get("objective") for c in decision.configurations]
        self.assertNotIn(None, survivors)
        self.assertEqual(sorted(survivors), [1, 2, 3])


class TestShortWaveDoesNotStallTheBarrier(unittest.TestCase):
    """
    A rung waits for the number of Configurations that is really coming.

    Selection is asked for n points but publishes fewer whenever it cannot break
    a duplicate by resampling or the search space is nearly exhausted. A barrier
    that insisted on n would never release.
    """

    minimization = [True]

    def _measure(self, controller, values):
        decision = None
        for value in values:
            decision = controller.on_configuration_measured(FakeConfiguration(value), self.minimization)
        return decision

    def test_short_wave_lowers_the_expectation(self):
        controller = SuccessiveHalving(sh_config(eta=3, n=9))
        start = controller.start()
        self.assertEqual(start.number_of_configurations, 9)

        # Selection could only publish 6 of the 9 requested points.
        self.assertEqual(controller.on_wave_dispatched(6, self.minimization, start.token).kind,
                         DecisionKind.WAIT)
        self.assertEqual(self._measure(controller, [5, 3, 8, 1, 7]).kind, DecisionKind.WAIT)
        decision = self._measure(controller, [2])
        self.assertEqual(decision.kind, DecisionKind.PROMOTE)
        self.assertEqual(sorted(c.results["objective"] for c in decision.configurations), [1, 2, 3])

    def test_report_arriving_after_every_result_still_closes_the_rung(self):
        # The wave is published, all of it comes back, and only then does the
        # dispatch report land - the barrier must not be left waiting.
        controller = SuccessiveHalving(sh_config(eta=3, n=9))
        start = controller.start()
        self.assertEqual(self._measure(controller, [5, 3, 8, 1]).kind, DecisionKind.WAIT)
        decision = controller.on_wave_dispatched(4, self.minimization, start.token)
        self.assertEqual(decision.kind, DecisionKind.PROMOTE)
        # 4 raced, the ladder keeps 3 of them - still the ladder's count, since
        # it is the smaller of the two.
        self.assertEqual(sorted(c.results["objective"] for c in decision.configurations), [1, 3, 5])

    def test_full_wave_changes_nothing(self):
        controller = SuccessiveHalving(sh_config(eta=3, n=9))
        start = controller.start()
        self.assertEqual(controller.on_wave_dispatched(9, self.minimization, start.token).kind,
                         DecisionKind.WAIT)
        self.assertEqual(self._measure(controller, [5, 3, 8, 1, 7, 2, 9, 4]).kind, DecisionKind.WAIT)
        self.assertEqual(self._measure(controller, [6]).kind, DecisionKind.PROMOTE)

    def test_stale_report_is_dropped(self):
        # A report for a rung that has already closed must not shrink its successor.
        controller = SuccessiveHalving(sh_config(eta=3, n=9))
        start = controller.start()
        promote = self._measure(controller, [5, 3, 8, 1, 7, 2, 9, 4, 6])
        self.assertEqual(promote.kind, DecisionKind.PROMOTE)
        self.assertNotEqual(promote.token, start.token)

        self.assertEqual(controller.on_wave_dispatched(1, self.minimization, start.token).kind,
                         DecisionKind.WAIT)
        # The promotion rung still waits for all 3 survivors.
        self.assertEqual(self._measure(controller, [3, 1]).kind, DecisionKind.WAIT)
        self.assertEqual(self._measure(controller, [2]).kind, DecisionKind.PROMOTE)

    def test_promotion_never_exceeds_what_raced(self):
        # Only 2 of 9 were dispatched, but the ladder wants to keep 3. Promoting
        # 3 would hand the next rung an expectation of 3 that can never be met.
        controller = SuccessiveHalving(sh_config(eta=3, n=9))
        start = controller.start()
        controller.on_wave_dispatched(2, self.minimization, start.token)
        decision = self._measure(controller, [5, 3])
        self.assertEqual(decision.kind, DecisionKind.PROMOTE)
        self.assertEqual(len(decision.configurations), 2)
        # Rung 1 waits for the 2 survivors it was actually given, not the 3 its
        # own ladder entry names.
        self.assertEqual(self._measure(controller, [3]).kind, DecisionKind.WAIT)
        self.assertEqual(self._measure(controller, [5]).kind, DecisionKind.PROMOTE)
        self.assertEqual(self._measure(controller, [3]).kind, DecisionKind.STOP)

    def test_empty_wave_abandons_the_bracket(self):
        controller = SuccessiveHalving(sh_config(eta=3, n=9, number_of_brackets=2))
        start = controller.start()
        decision = controller.on_wave_dispatched(0, self.minimization, start.token)
        self.assertEqual(decision.kind, DecisionKind.NEW_BRACKET)
        self.assertEqual(decision.number_of_configurations, 5)

    def test_empty_wave_on_the_last_bracket_stops(self):
        controller = SuccessiveHalving(sh_config(eta=3, n=9, number_of_brackets=1))
        start = controller.start()
        self.assertEqual(controller.on_wave_dispatched(0, self.minimization, start.token).kind,
                         DecisionKind.STOP)


class TestRungTimeout(unittest.TestCase):
    """
    The safety net for a measurement that is never coming back: a Task terminated
    as a straggler never reports a result, so its Configuration never returns and
    a count-based barrier cannot tell "lost" from "still running".
    """

    minimization = [True]

    def test_absent_by_default(self):
        self.assertIsNone(SuccessiveHalving(sh_config()).rung_timeout_seconds)

    def test_read_from_the_description(self):
        controller = SuccessiveHalving(sh_config(rung_timeout=90.0))
        self.assertEqual(controller.rung_timeout_seconds, 90.0)

    def test_timeout_ranks_what_arrived(self):
        controller = SuccessiveHalving(sh_config(eta=3, n=9, rung_timeout=1.0))
        start = controller.start()
        for value in [5, 3, 8, 1]:
            controller.on_configuration_measured(FakeConfiguration(value), self.minimization)
        decision = controller.on_rung_timeout(self.minimization, start.token)
        self.assertEqual(decision.kind, DecisionKind.PROMOTE)
        # The 5 Configurations that never came back are simply not ranked.
        self.assertEqual(sorted(c.results["objective"] for c in decision.configurations), [1, 3, 5])

    def test_stale_timeout_is_dropped(self):
        controller = SuccessiveHalving(sh_config(eta=3, n=9, rung_timeout=1.0))
        start = controller.start()
        for value in [5, 3, 8, 1, 7, 2, 9, 4, 6]:
            controller.on_configuration_measured(FakeConfiguration(value), self.minimization)
        # The rung closed on its own; the timer for it fires a moment later.
        self.assertEqual(controller.on_rung_timeout(self.minimization, start.token).kind,
                         DecisionKind.WAIT)

    def test_timeout_without_any_result_abandons_the_bracket(self):
        controller = SuccessiveHalving(sh_config(eta=3, n=9, number_of_brackets=2, rung_timeout=1.0))
        start = controller.start()
        decision = controller.on_rung_timeout(self.minimization, start.token)
        self.assertEqual(decision.kind, DecisionKind.NEW_BRACKET)
        self.assertEqual(decision.number_of_configurations, 5)


class TestLateArrivals(unittest.TestCase):
    """
    A rung closed by a timeout leaves its stragglers running, so results keep
    arriving after the last bracket is done - and by then there is no bracket
    left for them to belong to.
    """

    minimization = [True]

    def _finish_single_bracket(self, controller):
        for value in [5, 3, 8, 1, 7, 2, 9, 4, 6]:
            controller.on_configuration_measured(FakeConfiguration(value), self.minimization)
        for value in [3, 1, 2]:
            controller.on_configuration_measured(FakeConfiguration(value), self.minimization)
        return controller.on_configuration_measured(FakeConfiguration(1), self.minimization)

    def test_result_after_stop_is_ignored(self):
        controller = SuccessiveHalving(sh_config(eta=3, n=9, number_of_brackets=1))
        controller.start()
        self.assertEqual(self._finish_single_bracket(controller).kind, DecisionKind.STOP)
        # No bracket left to index; the straggler must not blow up the consumer.
        self.assertEqual(controller.on_configuration_measured(
            FakeConfiguration(0.1), self.minimization).kind, DecisionKind.WAIT)

    def test_timeout_after_stop_is_ignored(self):
        controller = SuccessiveHalving(sh_config(eta=3, n=9, number_of_brackets=1, rung_timeout=1.0))
        controller.start()
        self.assertEqual(self._finish_single_bracket(controller).kind, DecisionKind.STOP)
        self.assertEqual(controller.on_rung_timeout(self.minimization).kind, DecisionKind.WAIT)

    def test_result_for_a_closed_rung_is_not_counted_in_the_next(self):
        controller = SuccessiveHalving(sh_config(eta=3, n=9, rung_timeout=1.0))
        start = controller.start()
        for value in [5, 3, 8, 1]:
            controller.on_configuration_measured(FakeConfiguration(value), self.minimization)
        promote = controller.on_rung_timeout(self.minimization, start.token)
        self.assertEqual(promote.kind, DecisionKind.PROMOTE)

        straggler = FakeConfiguration(0.1)
        straggler.rung_token = start.token
        self.assertEqual(controller.on_configuration_measured(straggler, self.minimization).kind,
                         DecisionKind.WAIT)
        # Rung 1 still waits for all of its own survivors.
        for survivor in promote.configurations[:-1]:
            survivor.rung_token = promote.token
            self.assertEqual(controller.on_configuration_measured(survivor, self.minimization).kind,
                             DecisionKind.WAIT)
        promote.configurations[-1].rung_token = promote.token
        self.assertEqual(controller.on_configuration_measured(
            promote.configurations[-1], self.minimization).kind, DecisionKind.PROMOTE)

    def test_dispatch_report_after_stop_is_ignored(self):
        controller = SuccessiveHalving(sh_config(eta=3, n=9, number_of_brackets=1))
        controller.start()
        self.assertEqual(self._finish_single_bracket(controller).kind, DecisionKind.STOP)
        self.assertEqual(controller.on_wave_dispatched(3, self.minimization).kind,
                         DecisionKind.WAIT)


if __name__ == "__main__":
    unittest.main()
