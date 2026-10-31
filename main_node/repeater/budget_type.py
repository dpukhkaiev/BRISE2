__doc__ = """
    What one unit of a rung budget buys.

    RepetitionManager.BudgetSchedule declares a geometric ladder of budgets and a
    BudgetType that says how a Configuration's budget b is spent:

    * "repetitions" (the default, and the only reading a Target System without a
      budget of its own can serve): b is the number of repetition Tasks. A
      promotion buys a tighter estimate of the same quantity - with a
      deterministic Target System it buys nothing at all.

    * "task_time": b scales the budget one Task itself gets, where
      Context.TaskConfiguration.Scenario.Budget.Amount is one unit. A promotion
      buys the search inside the Task more of whatever that Budget counts, so one
      Task per rung is enough. This is the multi-fidelity reading Hyperband
      assumes, and the only one under which a rung ladder can improve solution
      quality rather than just its confidence.
"""
from collections.abc import Mapping
from copy import deepcopy
from typing import Optional

REPETITIONS = "repetitions"
TASK_TIME = "task_time"


def budget_schedule(experiment_description: Mapping) -> Optional[Mapping]:
    """The declared ladder, or None when the Experiment has no multi-fidelity budget."""
    return (experiment_description.get("RepetitionManager") or {}).get("BudgetSchedule") or None


def budget_type(experiment_description: Mapping) -> str:
    """The BudgetType of the declared ladder, "repetitions" if there is none."""
    return (budget_schedule(experiment_description) or {}).get("BudgetType", REPETITIONS)


def is_task_time_budget(experiment_description: Mapping) -> bool:
    """Does a rung budget scale the Task's own budget instead of repeating it?"""
    return budget_type(experiment_description) == TASK_TIME


def scale_scenario_budget(scenario: Mapping, task_budget: Optional[int]) -> Mapping:
    """
    The Scenario one Task is measured with when its Configuration sits on a rung
    of `task_budget` units: the declared Budget.Amount is one unit.

    Returns the Scenario unchanged for the lowest rung and for Configurations
    without a budget (the default Configuration), so a Task always carries at
    least one unit.
    """
    if not task_budget or task_budget <= 1:
        return scenario
    scaled = deepcopy(scenario)
    scaled["Budget"]["Amount"] = scenario["Budget"]["Amount"] * task_budget
    return scaled
