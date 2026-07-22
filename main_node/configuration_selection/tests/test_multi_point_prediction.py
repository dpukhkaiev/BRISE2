"""
Unit tests for the multi-point-proposal arithmetic in ConfigurationSelection.

These cover `_regular_prediction`, which turns a `worker_capacity` request
(`needed_configs`) into configurations by asking the predictor for proposals of
NumberOfPoints (N) points each. The behavior to lock in:

  * async / N=1 default               -> 1 config from 1 build (unchanged)
  * batched, BatchSize == N           -> N configs from a SINGLE build
  * BatchSize a multiple of N         -> BatchSize configs, BatchSize/N builds
  * BatchSize not a multiple of N     -> exactly BatchSize configs (sliced tail)
"""
import os
import threading
from unittest.mock import MagicMock

# `send_new_configurations_to_measure` only skips the RabbitMQ publish when the
# process runs in unit-test mode; set it before anything touches the broker.
os.environ["TEST_MODE"] = "UNIT_TEST"

from configuration_selection.configuration_selection import ConfigurationSelection
from core_entities.configuration import Configuration


def _make_selection(points_per_build: int):
    """
    Build a ConfigurationSelection without its heavy __init__ (no DB / RabbitMQ),
    wiring just enough state for `_regular_prediction`. Each `predict` call
    returns `points_per_build` distinct sentinel configs, and records its calls
    so we can assert how many surrogate builds happened.
    """
    selection = ConfigurationSelection.__new__(ConfigurationSelection)
    selection.experiment = MagicMock()
    selection.experiment.measured_configurations = []

    predictor = MagicMock()
    call_counter = {"n": 0}

    def _predict(measured_configurations, *args, **kwargs):
        call_counter["n"] += 1
        build_id = call_counter["n"]
        return [f"c{build_id}_{i}" for i in range(points_per_build)]

    predictor.predict.side_effect = _predict
    selection.predictor = predictor
    return selection, predictor


def test_async_default_single_point():
    """worker_capacity=1, N=1 -> 1 config from exactly one build (today's path)."""
    selection, predictor = _make_selection(points_per_build=1)
    result = selection._regular_prediction(needed_configs=1)
    assert len(result) == 1
    assert predictor.predict.call_count == 1


def test_multi_point_single_build():
    """worker_capacity=N, N=N -> N configs from ONE surrogate build."""
    selection, predictor = _make_selection(points_per_build=5)
    result = selection._regular_prediction(needed_configs=5)
    assert len(result) == 5
    # The whole wave comes from a single build (true multi-point proposal).
    assert predictor.predict.call_count == 1
    # All five points of the wave are distinct.
    assert len(set(result)) == 5


def test_batch_is_multiple_of_points():
    """BatchSize=6, N=2 -> 6 configs from 3 builds."""
    selection, predictor = _make_selection(points_per_build=2)
    result = selection._regular_prediction(needed_configs=6)
    assert len(result) == 6
    assert predictor.predict.call_count == 3


def test_batch_not_multiple_of_points_slices_tail():
    """BatchSize=5, N=2 -> exactly 5 configs (last build contributes a sliced tail)."""
    selection, predictor = _make_selection(points_per_build=2)
    result = selection._regular_prediction(needed_configs=5)
    assert len(result) == 5
    # ceil(5/2) = 3 builds; the third build is sliced to a single point.
    assert predictor.predict.call_count == 3


# ---------------------------------------------------------------------------
# Intra-wave de-duplication (the whole `send_new_configurations_to_measure`
# path, not just the arithmetic).
#
# On a small, discrete search space (e.g. the flat Energy space:
# frequency x threads) with a deterministic surrogate, the N>1 build batches
# produced within ONE wave frequently propose the SAME point more than once:
# `_regular_prediction` calls `predict()` several times on the *same*
# measured_configurations, so two builds can return an identical config.
#
# These tests drive the real dedup logic with real `Configuration` objects so
# `__eq__` (parameters-based) behaves authentically, and assert the property a
# wave must uphold: it never sends the same configuration to be measured twice.
# ---------------------------------------------------------------------------
EXPERIMENT_ID = "multi-point-test"


def _cfg(frequency, threads, config_type=Configuration.Type.PREDICTED):
    """A realistic flat-Energy-space configuration (params drive `__eq__`)."""
    return Configuration(
        {"frequency": float(frequency), "threads": int(threads)},
        config_type,
        EXPERIMENT_ID,
    )


def _params(configs):
    """Hashable view of each config's parameters, for duplicate detection."""
    return [tuple(sorted(c.parameters.items())) for c in configs]


class _FakeSearchSpace:
    def __init__(self):
        self.size = 10_000  # large -> never hits the "space exhausted" branch
        self.is_flat = True

    def transform_flat_parameters_to_hierarchic(self, parameters):
        # The flat->hierarchic transform is irrelevant to de-duplication; keep
        # the parameters as-is so the test stays focused on the dedup logic.
        return parameters


class _FakeExperiment:
    def __init__(self):
        self.unique_id = EXPERIMENT_ID
        self.search_space = _FakeSearchSpace()
        self.evaluated_configurations = []
        self.measured_configurations = []

    def add_evaluated_configuration_to_experiment(self, configuration):
        self.evaluated_configurations.append(configuration)

    def update_model_state(self, model_state):
        pass


def _make_full_selection(number_of_points, scripted_builds):
    """
    Wire a ConfigurationSelection that exercises the FULL selection path
    (`send_new_configurations_to_measure`) without DB / RabbitMQ.

    `scripted_builds` is a list of lists: each inner list is what one surrogate
    build (one `predict()` call) proposes, consumed in order. A `predict(...,
    sample=True)` resample call instead returns a brand-new, never-seen config,
    mimicking the random sampler used to break duplicates.
    """
    selection = ConfigurationSelection.__new__(ConfigurationSelection)
    selection.experiment = _FakeExperiment()
    selection.sub = MagicMock()
    selection.transfer_is_enabled = False
    selection._selection_lock = threading.Lock()
    selection.logger = MagicMock()

    predictor = MagicMock()
    model = MagicMock()
    model.candidate_selector.number_of_points = number_of_points
    predictor.mapping_region_model = {("region",): model}

    builds = iter(scripted_builds)
    resample_counter = {"n": 0}

    def _predict(measured_configurations, sample=False, *args, **kwargs):
        if sample:
            resample_counter["n"] += 1
            # A fresh point outside any scripted/seeded parameter range.
            return [_cfg(9000 + resample_counter["n"], 99,
                         Configuration.Type.FROM_SELECTOR)]
        return list(next(builds))

    predictor.predict.side_effect = _predict
    selection.predictor = predictor
    return selection


def _wave_body(worker_capacity):
    import json
    return json.dumps({"worker_capacity": worker_capacity}).encode()


def test_wave_of_distinct_points_is_passed_through():
    """Control: when every build proposes distinct points, all N are kept."""
    a, b, c, d, e = (_cfg(2900, 32), _cfg(1300, 25), _cfg(2900, 20),
                     _cfg(1900, 18), _cfg(2400, 8))
    selection = _make_full_selection(
        number_of_points=2,
        scripted_builds=[[a, b], [c, d], [e]],  # worker_capacity=5, N=2
    )
    to_evaluate, _ = selection.send_new_configurations_to_measure(
        "", "", "", _wave_body(5))
    assert len(to_evaluate) == 5
    assert len(set(_params(to_evaluate))) == 5


def test_no_duplicate_config_is_measured_within_one_wave():
    """
    A point proposed by two different builds in the SAME wave must not be sent
    to be measured twice. Reproduces the deterministic-surrogate case where
    `predict()` returns the same best point across builds.
    """
    repeated = _cfg(2900, 32)
    selection = _make_full_selection(
        number_of_points=2,
        # Build 1 and build 2 both propose `repeated` -> intra-wave duplicate.
        scripted_builds=[[repeated, _cfg(1300, 25)],
                         [repeated, _cfg(1900, 18)],
                         [_cfg(2400, 8)]],
    )
    to_evaluate, hierarchical = selection.send_new_configurations_to_measure(
        "", "", "", _wave_body(5))

    # The wave must not dispatch the same configuration twice.
    assert len(_params(to_evaluate)) == len(set(_params(to_evaluate))), (
        f"Duplicate configuration dispatched within one wave: "
        f"{_params(to_evaluate)}")
    # Every dispatched config is registered exactly once as evaluated.
    assert len(selection.experiment.evaluated_configurations) == len(to_evaluate)
    assert len(hierarchical) == len(to_evaluate)


def test_wave_shrinks_when_no_distinct_resample_is_available():
    """
    When a proposed point duplicates an already-evaluated one and the sampler
    can only ever offer that same point (a nearly-exhausted space), the point
    is skipped rather than dispatched or retried forever: the wave returns
    fewer than N configs.
    """
    evaluated = _cfg(2900, 32)
    selection = _make_full_selection(number_of_points=2, scripted_builds=[])
    # This point was measured in a previous wave.
    selection.experiment.evaluated_configurations.append(evaluated)
    selection.experiment.measured_configurations.append(evaluated)

    fresh = _cfg(1300, 25)

    def _predict(measured_configurations, sample=False, *args, **kwargs):
        if sample:
            # The sampler can only offer the already-evaluated point.
            return [_cfg(2900, 32)]
        # One build (worker_capacity=2, N=2): a fresh point + a duplicate.
        return [fresh, _cfg(2900, 32)]

    selection.predictor.predict.side_effect = _predict

    to_evaluate, _ = selection.send_new_configurations_to_measure(
        "", "", "", _wave_body(2))

    # The duplicate is dropped (no distinct resample); only the fresh point
    # survives, and the call terminates (no infinite resample loop).
    assert _params(to_evaluate) == _params([fresh])
