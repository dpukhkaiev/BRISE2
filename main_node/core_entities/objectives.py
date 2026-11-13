from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterator, List, Mapping, Tuple


@dataclass(frozen=True)
class Objective:
    """
    One objective of the optimization problem, as declared in the Experiment Description
    (Context.TaskConfiguration.Objectives).
    """
    name: str
    minimization: bool
    data_type: str
    min_expected_value: float
    max_expected_value: float

    @property
    def sign(self) -> float:
        """1 for a minimized objective, -1 for a maximized one: value * sign is to be minimized."""
        return 1.0 if self.minimization else -1.0

    @property
    def expected_range(self) -> Tuple[float, float]:
        return self.min_expected_value, self.max_expected_value


@dataclass(frozen=True)
class Objectives:
    """
    The objectives of an experiment, in the order of the Experiment Description.
    """
    objectives: Tuple[Objective, ...]

    @staticmethod
    def from_description(description: Mapping[str, Mapping]) -> Objectives:
        """
        :param description: Context.TaskConfiguration.Objectives, keyed by the objectives' names.
        :return: the objectives, in the order of the description.
        :raises ValueError: if the Name of an objective differs from its key.
        """
        objectives = []
        for key, objective in description.items():
            if objective["Name"] != key:
                raise ValueError(f"The name of the objective '{key}' is '{objective['Name']}'; "
                                 f"the key of an objective in the Experiment Description is its name.")
            objectives.append(Objective(name=key,
                                        minimization=objective["Minimization"],
                                        data_type=objective["DataType"],
                                        min_expected_value=objective["MinExpectedValue"],
                                        max_expected_value=objective["MaxExpectedValue"]))
        return Objectives(tuple(objectives))

    def to_description(self) -> Dict[str, Dict]:
        return {o.name: {"Name": o.name,
                         "DataType": o.data_type,
                         "Minimization": o.minimization,
                         "MinExpectedValue": o.min_expected_value,
                         "MaxExpectedValue": o.max_expected_value} for o in self.objectives}

    @property
    def names(self) -> List[str]:
        return [o.name for o in self.objectives]

    def by_name(self, name: str) -> Objective:
        for objective in self.objectives:
            if objective.name == name:
                return objective
        raise KeyError(name)

    def __iter__(self) -> Iterator[Objective]:
        return iter(self.objectives)

    def __len__(self) -> int:
        return len(self.objectives)

    def is_better(self, results: Mapping[str, float], other_results: Mapping[str, float]) -> bool:
        """
        Comparison of the results of two configurations, each objective in its own direction. The results are better
        unless the other results dominate them. Equal results, and results that do not dominate each other, count as better.
        :param results: the results of the newcomer, keyed by the objectives' names.
        :param other_results: the results to compare with, e.g. those of the current best configuration.
        """
        other_is_no_worse_everywhere = all(other_results[o.name] * o.sign <= results[o.name] * o.sign
                                           for o in self.objectives)
        other_is_better_somewhere = any(other_results[o.name] * o.sign < results[o.name] * o.sign
                                        for o in self.objectives)
        other_dominates = other_is_no_worse_everywhere and other_is_better_somewhere
        return not other_dominates
