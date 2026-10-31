import functools
import threading
from typing import List, Optional

from configuration_racing.racing_abs import AbstractRacing, RacingDecision
from core_entities.configuration import Configuration
from repeater.budget_schedule import HyperbandSchedule


class SuccessiveHalving(AbstractRacing):
    """
    Synchronous, barrier-based Successive Halving driven by the Hyperband outer loop.

    Each bracket races its own number of Configurations over its own geometric
    budget ladder, taken from HyperbandSchedule: the first bracket starts many
    Configurations at MinBudget, every following one starts fewer at a higher
    budget. A rung is a barrier: only once every Configuration in it has reached
    the rung budget are they ranked and the top 1/Eta promoted to the next rung
    with more budget. When a bracket cannot promote anyone, the next bracket
    restarts at rung 0 with a fresh proposal, until NumberOfBrackets are done.

    A rung waits for what was really dispatched, not for what the schedule asked
    for: Selection reports its published count, a promotion expects its own
    survivors, and an optional RungTimeout ranks whatever arrived. `_rung_token`
    dates every rung, and every Configuration dispatched for it, so neither a late
    report nor a late result can be applied to its successor.

    The strategy is deliberately transport-free: it consumes measured
    Configurations and emits RacingDecisions; the core turns those into messages.
    The budget a rung hands out is spent by the RepetitionManager
    (BudgetAwareRepeater, Configuration.task_budget).
    """

    def __init__(self, experiment_description: dict):
        super().__init__()
        parameters = experiment_description["Racing"]["SuccessiveHalving"]
        # The ladder belongs to the RepetitionManager; Racing only walks it.
        ladder = experiment_description["RepetitionManager"]["BudgetSchedule"]
        self.eta = int(ladder["Eta"])
        self.number_of_brackets = int(parameters["NumberOfBrackets"])
        self.schedule = HyperbandSchedule(
            eta=self.eta,
            n=int(parameters["N"]),
            min_budget=int(ladder["MinBudget"]),
            max_budget=int(ladder["MaxBudget"]),
            number_of_brackets=self.number_of_brackets,
        )
        rung_timeout = parameters.get("RungTimeout") or {}
        self._rung_timeout_seconds = (float(rung_timeout["TimeoutInSeconds"])
                                      if "TimeoutInSeconds" in rung_timeout else None)

        # Shared between the core's result consumer and the Selection thread.
        self._lock = threading.Lock()
        self._current_bracket = 0
        self._current_rung = 0
        self._rung_token = 0
        # A timed-out rung leaves measurements running, so results still arrive
        # after the last bracket - when there is no bracket left to index.
        self._is_finished = False
        # Seeded from the schedule, corrected down by what was really dispatched.
        self._expected_in_rung = 0
        self._finished_in_rung: List[Configuration] = []

    @property
    def rung_timeout_seconds(self) -> Optional[float]:
        return self._rung_timeout_seconds

    def start(self) -> RacingDecision:
        with self._lock:
            ladders = [[(rung.n_configurations, rung.budget) for rung in bracket.rungs]
                       for bracket in self.schedule]
            self.logger.info(f"Starting Hyperband: {self.number_of_brackets} bracket(s), "
                             f"rung ladders (n, budget) = {ladders}.")
            return self._start_bracket()

    def on_configuration_measured(self, configuration: Configuration,
                                  objectives_minimization: List[bool]) -> RacingDecision:
        with self._lock:
            if self._is_finished:
                self.logger.info(f"Racing is over; {configuration} arrived too late "
                                 f"to race and is only recorded in the Experiment.")
                return RacingDecision.wait()
            if configuration.rung_token is not None and configuration.rung_token != self._rung_token:
                self.logger.info(f"{configuration} was measured for rung token "
                                 f"{configuration.rung_token} but the run is on token "
                                 f"{self._rung_token}; it is only recorded in the Experiment.")
                return RacingDecision.wait()
            self._finished_in_rung.append(configuration)
            if len(self._finished_in_rung) < self._expected_in_rung:
                return RacingDecision.wait()
            return self._close_rung(objectives_minimization, reason="complete")

    def on_wave_dispatched(self, number_of_configurations: int,
                           objectives_minimization: List[bool],
                           token: Optional[int] = None) -> RacingDecision:
        with self._lock:
            if self._is_finished:
                return RacingDecision.wait()
            if token is not None and token != self._rung_token:
                self.logger.debug(f"Ignoring a dispatch report of {number_of_configurations} "
                                  f"Configuration(s) for rung token {token}; the run is on "
                                  f"token {self._rung_token} already.")
                return RacingDecision.wait()
            if number_of_configurations >= self._expected_in_rung:
                return RacingDecision.wait()

            self.logger.warning(
                f"Bracket {self._current_bracket}, rung {self._current_rung}: Selection published "
                f"{number_of_configurations} of {self._expected_in_rung} requested Configuration(s); "
                f"racing the rung with what was dispatched.")
            self._expected_in_rung = number_of_configurations
            if len(self._finished_in_rung) < self._expected_in_rung:
                return RacingDecision.wait()
            return self._close_rung(objectives_minimization, reason="short wave")

    def on_rung_timeout(self, objectives_minimization: List[bool],
                        token: Optional[int] = None) -> RacingDecision:
        with self._lock:
            if self._is_finished or (token is not None and token != self._rung_token):
                return RacingDecision.wait()
            self.logger.warning(
                f"Bracket {self._current_bracket}, rung {self._current_rung} timed out after "
                f"{self._rung_timeout_seconds}s with {len(self._finished_in_rung)} of "
                f"{self._expected_in_rung} Configuration(s) measured; a measurement was most "
                f"likely lost. Ranking what arrived.")
            return self._close_rung(objectives_minimization, reason="timed out")

    def _close_rung(self, objectives_minimization: List[bool], reason: str) -> RacingDecision:
        """Rank the finished rung and decide what follows it. Caller holds the lock."""
        finished = self._finished_in_rung
        self._finished_in_rung = []
        if not finished:
            self.logger.error(f"Bracket {self._current_bracket}, rung {self._current_rung} closed "
                              f"({reason}) without a measured Configuration; abandoning the bracket.")
            return self._advance_bracket()

        # Never promote more than raced: the next rung needs a count it can meet.
        number_to_promote = min(self._current_bracket_definition().survivors_after(self._current_rung),
                                len(finished))
        if number_to_promote >= 1:
            survivors = self._rank(finished, objectives_minimization)[:number_to_promote]
            previous_rung = self._current_rung
            self._advance_rung()
            budget = self._current_rung_definition().budget
            self._expected_in_rung = len(survivors)
            self.logger.info(f"Bracket {self._current_bracket}, rung {previous_rung} {reason}: "
                             f"promoting {len(survivors)} of {len(finished)} to rung "
                             f"{self._current_rung} at budget {budget}.")
            return RacingDecision.promote(survivors, budget, token=self._rung_token)
        return self._advance_bracket()

    def _advance_rung(self) -> None:
        self._current_rung += 1
        self._rung_token += 1

    def _advance_bracket(self) -> RacingDecision:
        self.logger.info(f"Bracket {self._current_bracket} complete.")
        self._current_bracket += 1
        self._current_rung = 0
        self._rung_token += 1
        if self._current_bracket >= self.number_of_brackets:
            self.logger.info("All Hyperband brackets complete.")
            self._expected_in_rung = 0
            self._is_finished = True
            return RacingDecision.stop()
        return self._start_bracket()

    def _start_bracket(self) -> RacingDecision:
        rung = self._current_rung_definition()
        self._finished_in_rung = []
        self._expected_in_rung = rung.n_configurations
        self.logger.info(f"Bracket {self._current_bracket} starts {rung.n_configurations} "
                         f"Configuration(s) at budget {rung.budget}.")
        return RacingDecision.new_bracket(rung.n_configurations, rung.budget,
                                          token=self._rung_token)

    def _current_bracket_definition(self):
        return self.schedule[self._current_bracket]

    def _current_rung_definition(self):
        return self._current_bracket_definition().rungs[self._current_rung]

    @staticmethod
    def _rank(configurations: List[Configuration],
              objectives_minimization: List[bool]) -> List[Configuration]:
        """Best first. Configurations without results (e.g. disabled) rank last."""
        def compare(left: Configuration, right: Configuration) -> int:
            if bool(left.results) != bool(right.results):
                return -1 if left.results else 1
            if not left.results:
                return 0
            if left.is_better(objectives_minimization, right):
                return -1
            if right.is_better(objectives_minimization, left):
                return 1
            return 0

        return sorted(configurations, key=functools.cmp_to_key(compare))
