import math
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Rung:
    n_configurations: int  # Configurations racing at this rung
    budget: int            # repetition tasks each of them is measured with


class BudgetSchedule:
    """
    The rung ladder of one Successive Halving bracket.

    From (eta, n, min_budget, max_budget) it derives the geometric schedule:
    rung k races n_k = floor(n * eta^-k) Configurations at budget
    b_k = min(min_budget * eta^k, max_budget), keeping the top
    n_{k+1} = floor(n_k / eta) survivors for the next rung. The ladder ends once a
    rung would keep fewer than one survivor, the budget reaches max_budget, or the
    optional number_of_rungs is reached.
    """

    def __init__(self, eta: int, n: int, min_budget: int, max_budget: int, number_of_rungs: int = None):
        if eta < 2:
            raise ValueError(f"Eta must be at least 2, got {eta}.")
        if n < 1:
            raise ValueError(f"N must be at least 1, got {n}.")
        if not 1 <= min_budget <= max_budget:
            raise ValueError(f"Budgets must satisfy 1 <= MinBudget <= MaxBudget, "
                             f"got MinBudget={min_budget}, MaxBudget={max_budget}.")
        self.eta = eta
        self.n = n
        self.min_budget = min_budget
        self.max_budget = max_budget
        self.rungs: List[Rung] = self._build(number_of_rungs)

    def _build(self, number_of_rungs: int = None) -> List[Rung]:
        rungs = []
        n_k = self.n
        budget_k = self.min_budget
        while True:
            rungs.append(Rung(n_configurations=n_k, budget=min(budget_k, self.max_budget)))
            n_next = n_k // self.eta
            if budget_k >= self.max_budget or n_next < 1 or len(rungs) == number_of_rungs:
                break
            n_k = n_next
            budget_k = budget_k * self.eta
        return rungs

    @property
    def number_of_rungs(self) -> int:
        return len(self.rungs)

    def survivors_after(self, rung_index: int) -> int:
        """How many Configurations are promoted out of rung `rung_index` (0 if it is the last)."""
        next_index = rung_index + 1
        return self.rungs[next_index].n_configurations if next_index < len(self.rungs) else 0


class HyperbandSchedule:
    """
    The bracket sequence of the Hyperband outer loop (Li et al., 2018).

    A bracket s races n_s Configurations over s+1 rungs, starting at budget
    b_s and ending at max_budget:

        s_max = floor(log_eta(max_budget / min_budget))
        n_s   = ceil(scale * (s_max + 1) / (s + 1) * eta^s)
        b_s   = min_budget * eta^(s_max - s)

    Brackets are emitted s_max, s_max - 1, ... 0, so the first one is the most
    aggressive (many Configurations, minimal budget) and the last one measures a
    few Configurations at full budget without any elimination. Once the s_max + 1
    brackets of a full Hyperband loop are exhausted, the cycle repeats.

    `n` anchors the widest bracket: bracket s_max races exactly n Configurations
    and all other brackets are scaled accordingly, so one proposal of
    NumberOfPoints = n points covers the rung 0 of every bracket. n = eta^s_max
    reproduces the textbook bracket sizes.
    """

    def __init__(self, eta: int, n: int, min_budget: int, max_budget: int, number_of_brackets: int):
        if number_of_brackets < 1:
            raise ValueError(f"NumberOfBrackets must be at least 1, got {number_of_brackets}.")
        self.eta = eta
        self.n = n
        self.min_budget = min_budget
        self.max_budget = max_budget
        self.s_max = max(0, int(math.log(max_budget / min_budget, eta) + 1e-9))
        self.brackets: List[BudgetSchedule] = [self._build_bracket(self._bracket_index(i))
                                               for i in range(number_of_brackets)]

    def _bracket_index(self, position: int) -> int:
        return self.s_max - position % (self.s_max + 1)

    def _build_bracket(self, s: int) -> BudgetSchedule:
        scale = self.n / self.eta ** self.s_max
        n_s = max(1, math.ceil(scale * (self.s_max + 1) / (s + 1) * self.eta ** s))
        b_s = self.min_budget * self.eta ** (self.s_max - s)
        return BudgetSchedule(eta=self.eta, n=n_s, min_budget=b_s,
                              max_budget=self.max_budget, number_of_rungs=s + 1)

    def __len__(self) -> int:
        return len(self.brackets)

    def __getitem__(self, index: int) -> BudgetSchedule:
        return self.brackets[index]
