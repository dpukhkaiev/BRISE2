import pandas as pd
import pytest

from core_entities.objectives import Objectives
from core_entities.search_space import FloatHyperparameter
from configuration_selection.model.optimizer.moea import MOEA
from configuration_selection.model.optimizer.random_search import RandomSearch
from configuration_selection.model.surrogate.surrogate_abs import Surrogate

X = FloatHyperparameter("x", 0, 0.0, 1.0)


class FunctionSurrogate(Surrogate):
    """
    Predicts Y1 = x and, for two objectives, Y2 = 1 - x (a trade-off) for a configuration given by its value of x.
    """

    def create(self, features, labels) -> bool:
        return True

    def predict(self, cfg: pd.Series, transform: bool = True) -> pd.DataFrame:
        return self.predict_batch(pd.DataFrame({"x": [cfg["x"]]}))

    def predict_batch(self, configurations: pd.DataFrame, transform: bool = True) -> pd.DataFrame:
        x = configurations["x"].reset_index(drop=True)
        predicted = pd.DataFrame({"Y1": x})
        if "Y2" in self.objectives.names:
            predicted["Y2"] = 1.0 - x
        return predicted


def _objectives(*minimizations):
    return Objectives.from_description({
        f"Y{i + 1}": {"Name": f"Y{i + 1}", "DataType": "float", "Minimization": m,
                      "MinExpectedValue": 0, "MaxExpectedValue": float("inf")} for i, m in enumerate(minimizations)})


def _random_search(objectives, sampling_size=60, value_transformers=None) -> RandomSearch:
    description = {"Instance": {"RandomSearch": {"SamplingSize": sampling_size}}}
    if value_transformers:
        description["ValueTransformers"] = value_transformers
    return RandomSearch(description, (X,), objectives)


def _moea(objectives) -> MOEA:
    description = {"Instance": {"MOEA": {"Generations": 40, "PopulationSize": 24, "Algorithms": ["de"]}}}
    return MOEA(description, (X,), objectives)


class TestRandomSearchRanking:

    @pytest.mark.parametrize("minimization", [True, False])
    def test_candidates_are_returned_best_first_for_a_single_objective(self, minimization):
        objectives = _objectives(minimization)
        optimizer = _random_search(objectives)

        result = optimizer.optimize(FunctionSurrogate({}, (X,), objectives))

        assert len(result) == 60
        assert list(result.index) == list(range(60))
        assert result["Y1"].is_monotonic_increasing == minimization
        assert result["Y1"].is_monotonic_decreasing != minimization

    def test_non_dominated_candidates_precede_dominated_ones_for_several_objectives(self):
        # Y1 = x is minimized and Y2 = 1 - x is maximized: both prefer a small x, so x alone decides the order
        objectives = _objectives(True, False)
        optimizer = _random_search(objectives)

        result = optimizer.optimize(FunctionSurrogate({}, (X,), objectives))

        assert result.iloc[0]["x"] == result["x"].min()

    def test_conflicting_objectives_keep_every_candidate_on_the_first_front(self):
        # both minimized: Y1 = x and Y2 = 1 - x trade off, so no candidate dominates another
        objectives = _objectives(True, True)
        optimizer = _random_search(objectives)

        candidates = pd.DataFrame({"x": [0.1, 0.5, 0.9, 0.6], "Y1": [0.1, 0.5, 0.9, 0.6], "Y2": [0.9, 0.5, 0.1, 0.6]})

        ranked = optimizer._rank_candidates(candidates, ["Y1", "Y2"])

        assert ranked["x"].iloc[-1] == 0.6  # the dominated candidate comes last
        assert set(ranked["x"].iloc[:3]) == {0.1, 0.5, 0.9}


class TestMoeaRanking:

    def test_a_minimized_objective_is_optimized_and_returned_best_first(self):
        objectives = _objectives(True)
        optimizer = _moea(objectives)

        result = optimizer.optimize(FunctionSurrogate({}, (X,), objectives))

        assert result["Y1"].is_monotonic_increasing
        assert result.iloc[0]["Y1"] < 0.01

    def test_a_maximized_objective_is_optimized_towards_its_maximum_and_returned_best_first(self):
        objectives = _objectives(False)
        optimizer = _moea(objectives)

        result = optimizer.optimize(FunctionSurrogate({}, (X,), objectives))

        assert result["Y1"].is_monotonic_decreasing
        assert result.iloc[0]["Y1"] > 0.99
        assert (result["Y1"] >= 0).all()  # predictions are reported as predicted, not negated
