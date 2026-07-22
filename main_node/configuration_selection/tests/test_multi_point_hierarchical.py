"""
Tests for multi-point proposal (NumberOfPoints = N > 1) in `Predictor.predict()`,
mainly on HIERARCHICAL (tree-shaped) search spaces.

The contract, independent of how it is implemented: with `NumberOfPoints = N`
a proposal returns exactly N configurations, each one a valid single root-to-leaf
branch of the tree (never a mix of parameters from mutually exclusive branches),
and every region is built at most once - the N points share the optimizer's work.

Instead of real sklearn surrogates each region's Model is a `_FakeModel` that
returns the realistic shape of a real build: N candidate rows sharing pandas
index 0, whose rows differ from one another the way a stochastic optimizer's
candidates do. This keeps the tests on the predictor's tree-walk logic - no DB,
RabbitMQ or sklearn.

Two search spaces are used:

    simple:                         deep (asymmetric depth):
      root_choice (L0)                root_choice (L0)
        ├─ catA → xa (L1)               ├─ catA → xa (L1)
        └─ catB → xb (L1)               └─ catB → sub (L1)
                                                   ├─ subX → xbx (L2)
                                                   └─ subY → xby (L2)
"""
import logging
from types import SimpleNamespace

import pandas as pd

from core_entities.configuration import Configuration
from core_entities.search_space import SearchSpace
from configuration_selection.model.predictor import Predictor
from configuration_selection.sampling.sampling_strategy_orchestrator import SamplingStrategyOrchestrator


_SIMPLE_DESCRIPTION = {
    "root_choice": {
        "catA": {"xa": {"Lower": 0.0, "Upper": 10.0, "Default": 5.0,
                        "Type": "FloatHyperparameter", "Level": 1}, "Type": "Category"},
        "catB": {"xb": {"Lower": 0.0, "Upper": 10.0, "Default": 5.0,
                        "Type": "FloatHyperparameter", "Level": 1}, "Type": "Category"},
        "Categories": ["Context.SearchSpace.root_choice.catA",
                       "Context.SearchSpace.root_choice.catB"],
        "Default": "Context.SearchSpace.root_choice.catA",
        "Type": "NominalHyperparameter", "Level": 0,
    },
    "Structure": {"Hierarchical": {}},
}
CAT_A = "Context.SearchSpace.root_choice.catA"
CAT_B = "Context.SearchSpace.root_choice.catB"
SIMPLE_BRANCH_LEAF = {CAT_A: "xa", CAT_B: "xb"}


_DEEP_DESCRIPTION = {
    "root_choice": {
        "catA": {"xa": {"Lower": 0.0, "Upper": 10.0, "Default": 5.0,
                        "Type": "FloatHyperparameter", "Level": 1}, "Type": "Category"},
        "catB": {
            "sub": {
                "subX": {"xbx": {"Lower": 0.0, "Upper": 10.0, "Default": 5.0,
                                 "Type": "FloatHyperparameter", "Level": 2}, "Type": "Category"},
                "subY": {"xby": {"Lower": 0.0, "Upper": 10.0, "Default": 5.0,
                                 "Type": "FloatHyperparameter", "Level": 2}, "Type": "Category"},
                "Categories": ["Context.SearchSpace.root_choice.catB.sub.subX",
                               "Context.SearchSpace.root_choice.catB.sub.subY"],
                "Default": "Context.SearchSpace.root_choice.catB.sub.subX",
                "Type": "NominalHyperparameter", "Level": 1,
            },
            "Type": "Category",
        },
        "Categories": ["Context.SearchSpace.root_choice.catA",
                       "Context.SearchSpace.root_choice.catB"],
        "Default": "Context.SearchSpace.root_choice.catA",
        "Type": "NominalHyperparameter", "Level": 0,
    },
    "Structure": {"Hierarchical": {}},
}
DEEP_SUB_X = "Context.SearchSpace.root_choice.catB.sub.subX"
DEEP_SUB_Y = "Context.SearchSpace.root_choice.catB.sub.subY"
DEEP_SUB_LEAF = {DEEP_SUB_X: "xbx", DEEP_SUB_Y: "xby"}


class _FakeModel:
    """
    Stand-in for a per-region Model. One call = one surrogate build + one
    optimizer run, returning N candidate rows that all share pandas index 0 (the
    shape a real build yields today). Rows differ from one another, and the
    per-call offset rotates them, standing in for a stochastic optimizer.
    """

    def __init__(self, region, number_of_points):
        self.region = region
        self.candidate_selector = SimpleNamespace(number_of_points=number_of_points)
        self.created_surrogates_descriptions_and_objectives_and_optimizer_descriptions = []
        self.time_to_build = None
        self._calls = 0

    def predict(self, region_hyperparameters, considered_configs):
        n = self.candidate_selector.number_of_points
        offset = self._calls
        self._calls += 1
        columns = {}
        for hp in self.region:
            if hp.get_type() in ("Nominal", "Ordinal"):
                categories = list(hp.categories)
                columns[hp.name] = [categories[(i + offset) % len(categories)] for i in range(n)]
            else:
                columns[hp.name] = [float((i + offset) % 10 + 1) for i in range(n)]
        columns["Y1"] = [0.1 * (i + 1) for i in range(n)]
        return pd.DataFrame(columns, index=[0] * n)


class _UnbuildableModel(_FakeModel):
    """A Model that cannot be built yet, as before the first measurement."""

    def predict(self, region_hyperparameters, considered_configs):
        return pd.DataFrame()


def _build_predictor(number_of_points, description=_SIMPLE_DESCRIPTION, model=_FakeModel):
    search_space = SearchSpace(description)
    sampling_description = {"MersenneTwister": {"Seed": 1, "Type": "mersenne_twister"}}
    sampling_strategy_orchestrator = SamplingStrategyOrchestrator()

    predictor = Predictor.__new__(Predictor)
    predictor.experiment_id = "hierarchical-multi-point-test"
    predictor.search_space = search_space
    predictor.window_size = 1.0
    predictor.hierarchical_models_dumps = []
    predictor.logger = logging.getLogger(__name__)
    predictor.mapping_region_model = {
        region: model(region, number_of_points) for region in search_space.regions
    }
    predictor.mapping_region_sampling_strategy = {
        region: sampling_strategy_orchestrator.get_sampling_strategy(sampling_description, region)
        for region in search_space.regions
    }
    predictor.store_model_dumps_to_db = lambda: None
    return predictor


def _assert_simple_branch(config):
    params = dict(config.parameters)
    expected_leaf = SIMPLE_BRANCH_LEAF[params["root_choice"]]
    assert set(params) == {"root_choice", expected_leaf}, (
        f"configuration is not a valid single branch: {params}")
    

def _assert_deep_branch(config):
    params = dict(config.parameters)
    if params["root_choice"] == CAT_A:
        assert set(params) == {"root_choice", "xa"}, params
    else:
        assert params["root_choice"] == CAT_B, params
        leaf = DEEP_SUB_LEAF[params["sub"]]
        assert set(params) == {"root_choice", "sub", leaf}, params


def test_hierarchical_single_point_is_valid():
    """Control: N = 1 yields exactly one valid single-branch configuration."""
    result = _build_predictor(number_of_points=1).predict([], sample=False)
    assert len(result) == 1
    _assert_simple_branch(result[0])


def test_hierarchical_multi_point_returns_exactly_n_configs():
    number_of_points = 2
    result = _build_predictor(number_of_points=number_of_points).predict([], sample=False)
    assert len(result) == number_of_points, (
        f"expected {number_of_points} configurations, got {len(result)}: "
        f"{[dict(c.parameters) for c in result]}")


def test_hierarchical_multi_point_configs_are_single_branch():
    result = _build_predictor(number_of_points=2).predict([], sample=False)
    for config in result:
        _assert_simple_branch(config)


def test_hierarchical_multi_point_covers_distinct_branches():
    """When the root build proposes two categories, the N points follow both."""
    result = _build_predictor(number_of_points=2).predict([], sample=False)
    chosen_branches = {dict(c.parameters)["root_choice"] for c in result}
    assert chosen_branches == {CAT_A, CAT_B}


def test_each_region_is_built_at_most_once_per_proposal():
    """
    The point of multi-point proposal: the N points share one optimizer run per
    region. A region is built only if a point activated it, and never twice.
    """
    predictor = _build_predictor(number_of_points=2)
    predictor.predict([], sample=False)

    builds = {region: model._calls for region, model in predictor.mapping_region_model.items()}
    assert all(calls <= 1 for calls in builds.values()), f"a region was built more than once: {builds}"
    # root + both branches the two points took.
    assert sum(builds.values()) == 3


def test_hierarchical_multi_point_supports_different_branches_and_depths():
    """Points may take branches of different depth, each remaining valid."""
    result = _build_predictor(number_of_points=2, description=_DEEP_DESCRIPTION).predict([], sample=False)
    assert len(result) == 2
    for config in result:
        _assert_deep_branch(config)
    depths = {len(dict(c.parameters)) for c in result}
    assert depths == {2, 3}, f"expected one shallow and one deep path, got depths {depths}"


# ---------------------------------------------------------------------------
# Sampling fallback. Until a surrogate can be built - the whole initial phase of
# an experiment - a region falls back to its sampling strategy. A wave still asks
# for N configurations, so the fallback has to serve N distinct points, not one.
# This path is shared by flat and hierarchical search spaces.
# ---------------------------------------------------------------------------
_FLAT_DESCRIPTION = {
    "frequency": {"Lower": 1200.0, "Upper": 2900.0, "Default": 2900.0,
                  "Type": "FloatHyperparameter", "Level": 0},
    "threads": {"Lower": 1, "Upper": 32, "Default": 32,
                "Type": "IntegerHyperparameter", "Level": 0},
    "Structure": {"Flat": {}},
}


def test_flat_sampling_fallback_yields_n_points():
    result = _build_predictor(number_of_points=2, description=_FLAT_DESCRIPTION,
                              model=_UnbuildableModel).predict([], sample=False)
    assert len(result) == 2
    assert all(c.type is Configuration.Type.FROM_SELECTOR for c in result)
    assert result[0].parameters != result[1].parameters


def test_hierarchical_sampling_fallback_yields_n_single_branch_points():
    result = _build_predictor(number_of_points=2, model=_UnbuildableModel).predict([], sample=False)
    assert len(result) == 2
    for config in result:
        _assert_simple_branch(config)
        assert config.type is Configuration.Type.FROM_SELECTOR


def test_proposed_values_are_native_python_types():
    """A configuration is stored in the database, which cannot encode numpy scalars."""
    result = _build_predictor(number_of_points=2).predict([], sample=False)
    for config in result:
        for value in list(config.parameters.values()) + config.predicted_result:
            assert type(value).__module__ == "builtins", f"{value!r} is a {type(value)}"


def test_sample_yields_a_single_point_regardless_of_n():
    """`sample=True` breaks a duplicate proposal; its caller wants exactly one point."""
    result = _build_predictor(number_of_points=2).predict([], sample=True)
    assert len(result) == 1
    _assert_simple_branch(result[0])
    assert result[0].type is Configuration.Type.FROM_SELECTOR
