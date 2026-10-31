import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional

from core_entities.configuration import Configuration


class DecisionKind(Enum):
    WAIT = auto()          # the current rung is not full yet; hold the loop
    PROMOTE = auto()       # re-dispatch the survivors at a higher budget
    NEW_BRACKET = auto()   # ask Selection for a fresh rung-0 proposal
    STOP = auto()          # the whole Racing run is finished


@dataclass
class RacingDecision:
    """
    What the core should do next, as decided by the Racing strategy.

    It is a passive value object: the strategy owns the state machine and returns
    a decision, the core (MainThread) performs the messaging side effect. This
    keeps the strategy free of RabbitMQ so it stays unit-testable.

    `token` dates the rung a decision opened, so a late report cannot be applied
    to its successor.
    """
    kind: DecisionKind
    configurations: List[Configuration] = field(default_factory=list)
    budget: Optional[int] = None
    number_of_configurations: Optional[int] = None
    token: Optional[int] = None

    @classmethod
    def wait(cls) -> "RacingDecision":
        return cls(DecisionKind.WAIT)

    @classmethod
    def promote(cls, configurations: List[Configuration], budget: int,
                token: Optional[int] = None) -> "RacingDecision":
        return cls(DecisionKind.PROMOTE, configurations=configurations, budget=budget, token=token)

    @classmethod
    def new_bracket(cls, number_of_configurations: int, budget: int,
                    token: Optional[int] = None) -> "RacingDecision":
        return cls(DecisionKind.NEW_BRACKET, budget=budget,
                   number_of_configurations=number_of_configurations, token=token)

    @classmethod
    def stop(cls) -> "RacingDecision":
        return cls(DecisionKind.STOP)


class AbstractRacing(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def start(self) -> RacingDecision:
        """First decision, taken once the default Configuration is measured."""

    @abstractmethod
    def on_configuration_measured(self, configuration: Configuration,
                                  objectives_minimization: List[bool]) -> RacingDecision:
        """Fold one freshly measured Configuration into the run and decide the next step."""

    def on_wave_dispatched(self, number_of_configurations: int,
                           objectives_minimization: List[bool],
                           token: Optional[int] = None) -> RacingDecision:
        """
        How many Configurations a NEW_BRACKET request actually produced. Selection
        may publish fewer than asked, so a counting strategy has to lower its
        expectation instead of waiting forever.
        """
        return RacingDecision.wait()

    def on_rung_timeout(self, objectives_minimization: List[bool],
                        token: Optional[int] = None) -> RacingDecision:
        """
        The current rung outlived `rung_timeout_seconds`. A Task terminated as a
        straggler never reports a result, and a barrier cannot tell that from
        "still running".
        """
        return RacingDecision.wait()

    @property
    def rung_timeout_seconds(self) -> Optional[float]:
        """Seconds before the core calls `on_rung_timeout`; None waits forever."""
        return None
