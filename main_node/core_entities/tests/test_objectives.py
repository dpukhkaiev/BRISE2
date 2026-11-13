import dataclasses
import json
import pickle
from pathlib import Path

import pytest

from core_entities.objectives import Objective, Objectives

PRODUCT_CONFIGURATIONS = sorted(
    (Path(__file__).parents[2] / "Resources" / "tests" / "test_cases_product_configurations").glob("*.json"))
assert PRODUCT_CONFIGURATIONS, "no product configurations found: an empty list would skip the parametrized test"


def _objective(name: str, minimization: bool = True, data_type: str = "float", lower=0, upper=float("inf")) -> dict:
    return {"Name": name, "DataType": data_type, "Minimization": minimization,
            "MinExpectedValue": lower, "MaxExpectedValue": upper}


def _objectives(**directions: str) -> Objectives:
    """Objectives named after the keywords, in their order, each "min" (minimized) or "max" (maximized)."""
    assert set(directions.values()) <= {"min", "max"}, f"unknown direction in {directions}"
    return Objectives.from_description({name: _objective(name, direction == "min") for name, direction in directions.items()})


class TestDescription:

    @pytest.mark.parametrize("path", PRODUCT_CONFIGURATIONS, ids=lambda path: path.name)
    def test_the_objectives_of_a_product_configuration_are_written_back_as_read(self, path):
        with open(path) as file:
            description = json.load(file)["Context"]["TaskConfiguration"]["Objectives"]

        objectives = Objectives.from_description(description)

        assert objectives.to_description() == description
        assert list(objectives.to_description()) == list(description)  # the order is kept

    def test_the_fields_of_an_objective_are_read_from_its_description(self):
        objectives = Objectives.from_description({"time": _objective("time", False, "int", 1, 10)})

        assert objectives.by_name("time") == Objective(
            name="time", minimization=False, data_type="int", min_expected_value=1, max_expected_value=10)

    def test_a_name_that_differs_from_its_key_is_rejected(self):
        # the key is the name; a stale description must fail at the start, not check the wrong objective
        description = {"test_f1_macro": _objective("test_f1_weighted")}

        with pytest.raises(ValueError, match="test_f1_macro"):
            Objectives.from_description(description)


class TestObjective:

    def test_the_sign_of_a_minimized_objective_is_positive_and_that_of_a_maximized_one_negative(self):
        assert Objective("a", True, "float", 0, 1).sign == 1
        assert Objective("a", False, "float", 0, 1).sign == -1

    def test_the_expected_range_is_the_lower_and_the_upper_bound(self):
        assert Objective("a", True, "float", 2, 7).expected_range == (2, 7)

    def test_an_objective_cannot_be_changed(self):
        # objectives are shared between surrogates, optimizers and models
        objective = Objective("a", True, "float", 0, 1)

        with pytest.raises(dataclasses.FrozenInstanceError):
            objective.minimization = False


class TestObjectives:

    def test_the_names_and_the_iteration_follow_the_order_of_the_description(self):
        objectives = _objectives(b="min", a="max", c="min")

        assert objectives.names == ["b", "a", "c"]
        assert [objective.name for objective in objectives] == ["b", "a", "c"]
        assert len(objectives) == 3

    def test_an_objective_is_found_by_its_name(self):
        objectives = _objectives(a="min", b="max")

        assert objectives.by_name("b").minimization is False

    def test_an_unknown_name_raises_a_key_error(self):
        with pytest.raises(KeyError):
            _objectives(a="min").by_name("b")

    def test_objectives_built_from_equal_descriptions_are_equal(self):
        # the Compositional model and the transfer of models compare the objectives of surrogates and optimizers
        assert _objectives(a="min", b="max") == _objectives(a="min", b="max")
        assert _objectives(a="min", b="max") != _objectives(a="min", b="min")

    def test_a_slice_of_objectives_equals_the_objectives_built_from_its_description(self):
        # Model builds one-objective slices
        objectives = _objectives(a="min", b="max")

        assert Objectives(tuple(objectives)[1:]) == _objectives(b="max")

    def test_the_union_of_objectives_equals_the_objectives_built_from_its_description(self):
        # CompositeSurrogate builds the union of the objectives of its surrogates
        union = Objectives(tuple(_objectives(a="min")) + tuple(_objectives(b="max")))

        assert union == _objectives(a="min", b="max")

    def test_objectives_survive_pickling(self):
        # surrogates, optimizers and models are pickled with their objectives
        objectives = _objectives(a="min", b="max")

        assert pickle.loads(pickle.dumps(objectives)) == objectives


class TestIsBetter:
    """
    A newcomer is better unless the other results dominate it: they are at least as good in every objective and strictly
    better in one, each objective in its own direction. Equal results count as better (the newcomer replaces the best).
    """

    def test_a_minimized_objective_is_better_when_lower(self):
        objectives = _objectives(a="min")

        assert objectives.is_better({"a": 1}, {"a": 2})
        assert not objectives.is_better({"a": 2}, {"a": 1})

    def test_a_maximized_objective_is_better_when_higher(self):
        objectives = _objectives(a="max")

        assert objectives.is_better({"a": 2}, {"a": 1})
        assert not objectives.is_better({"a": 1}, {"a": 2})

    def test_equal_results_count_as_better(self):
        assert _objectives(a="min").is_better({"a": 1}, {"a": 1})
        assert _objectives(a="min", b="max").is_better({"a": 1, "b": 1}, {"a": 1, "b": 1})

    def test_results_that_do_not_dominate_each_other_count_as_better(self):
        objectives = _objectives(a="min", b="min")

        assert objectives.is_better({"a": 1, "b": 5}, {"a": 2, "b": 3})
        assert objectives.is_better({"a": 2, "b": 3}, {"a": 1, "b": 5})

    def test_results_dominated_in_every_objective_are_not_better(self):
        objectives = _objectives(a="min", b="min")

        assert not objectives.is_better({"a": 2, "b": 4}, {"a": 1, "b": 3})
        assert objectives.is_better({"a": 1, "b": 3}, {"a": 2, "b": 4})

    def test_results_dominated_with_a_tie_in_one_objective_are_not_better(self):
        # (1, 3) against (1, 2): equal in a, worse in b
        objectives = _objectives(a="min", b="min")

        assert not objectives.is_better({"a": 1, "b": 3}, {"a": 1, "b": 2})
        assert objectives.is_better({"a": 1, "b": 2}, {"a": 1, "b": 3})

    def test_every_objective_is_compared_in_its_own_direction(self):
        # a is minimized, b maximized: (2, 5) is worse than (1, 10) in both
        objectives = _objectives(a="min", b="max")

        assert not objectives.is_better({"a": 2, "b": 5}, {"a": 1, "b": 10})
        assert objectives.is_better({"a": 1, "b": 10}, {"a": 2, "b": 5})

    def test_results_are_compared_by_name_not_by_position(self):
        objectives = _objectives(a="min", b="max")

        assert objectives.is_better({"b": 10, "a": 1}, {"a": 2, "b": 5})
