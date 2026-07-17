import pytest
from core_entities.experiment import Experiment

from test_gen_approach.integration_tests.helpers.db_utils import reset_database
from test_gen_approach.integration_tests.helpers.experiment_utils import (
    create_experiment_from_test_case,
    get_objective_count,
    get_parameter_types,
    load_phase1_config,
    PHASE1_OUTPUT_DIR,
)

test_new_configs = True

_phase1_configs = sorted(f.name for f in PHASE1_OUTPUT_DIR.glob("*.json"))
_brise_test_cases = list(range(15))
_test_ids = _phase1_configs if test_new_configs else _brise_test_cases


def _load_experiment(test_id, get_experiment):
    if test_new_configs:
        exp_desc, search_space = load_phase1_config(test_id)
        experiment = Experiment(exp_desc, search_space) if exp_desc and search_space else None
        return experiment, search_space
    else:
        experiment, _, search_space = create_experiment_from_test_case(test_id, get_experiment)
        return experiment, search_space


class TestExperimentInitialization:
    @pytest.mark.parametrize("test_id", _test_ids)
    def test_experiment_loads_successfully(self, test_id, get_experiment):
        reset_database()

        experiment, search_space = _load_experiment(test_id, get_experiment)

        assert experiment is not None, f"Experiment failed to load for: {test_id}"
        assert search_space is not None, f"Search space is None for: {test_id}"

    @pytest.mark.parametrize("test_id", _test_ids)
    def test_experiment_is_correct_type(self, test_id, get_experiment):
        reset_database()

        experiment, _ = _load_experiment(test_id, get_experiment)

        assert isinstance(
            experiment, Experiment
        ), f"Expected Experiment instance, but got {type(experiment)}"

    @pytest.mark.parametrize("test_id", _test_ids)
    def test_experiment_description_has_context(self, test_id, get_experiment):
        reset_database()

        experiment, _ = _load_experiment(test_id, get_experiment)

        assert experiment is not None
        assert (
            "Context" in experiment.description
        ), f"Missing 'Context' in experiment description for: {test_id}"

    @pytest.mark.parametrize("test_id", _test_ids)
    def test_experiment_description_has_task_configuration(self, test_id, get_experiment):
        reset_database()

        experiment, _ = _load_experiment(test_id, get_experiment)

        assert experiment is not None
        assert (
            "TaskConfiguration" in experiment.description["Context"]
        ), f"Missing 'TaskConfiguration' in Context for: {test_id}"

    @pytest.mark.parametrize("test_id", _test_ids)
    def test_objective_count_is_valid(self, test_id, get_experiment):
        reset_database()

        experiment, _ = _load_experiment(test_id, get_experiment)

        assert experiment is not None

        objective_count = get_objective_count(experiment)

        assert (
            objective_count is not None
        ), f"Failed to determine objective count for: {test_id}"
        assert objective_count in [
            1,
            2,
            5,
        ], f"Unexpected objective count {objective_count} for: {test_id}"

    @pytest.mark.parametrize("test_id", _test_ids)
    def test_parameter_types(self, test_id, get_experiment):
        reset_database()

        experiment, _ = _load_experiment(test_id, get_experiment)

        assert experiment is not None

        parameter_types = get_parameter_types(experiment)

        assert (
            parameter_types is not None
        ), f"Failed to determine parameter types for: {test_id}"
        assert parameter_types in [
            "2_float",
            "float_nom",
            "all_types",
        ], f"Unexpected parameter type '{parameter_types}' for: {test_id}"

    @pytest.mark.parametrize("test_id", _test_ids)
    def test_experiment_has_unique_id(self, test_id, get_experiment):
        reset_database()

        experiment, _ = _load_experiment(test_id, get_experiment)

        assert experiment is not None
        assert hasattr(
            experiment, "unique_id"
        ), f"Experiment missing unique_id for: {test_id}"
        assert (
            experiment.unique_id is not None
        ), f"Experiment unique_id is None for: {test_id}"
        assert (
            len(experiment.unique_id) > 0
        ), f"Experiment unique_id is empty for: {test_id}"
