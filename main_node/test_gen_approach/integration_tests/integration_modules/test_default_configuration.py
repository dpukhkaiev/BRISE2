import pytest
from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from test_gen_approach.integration_tests.helpers.db_utils import reset_database
from test_gen_approach.integration_tests.helpers.experiment_utils import (
    create_experiment_from_test_case,
    get_default_configuration,
    has_default_config_handler,
    has_transfer_learning,
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
        if exp_desc is None or search_space is None:
            return None, None
        experiment = Experiment(exp_desc, search_space)
        Configuration.set_task_config(
            experiment.description["Context"]["TaskConfiguration"]
        )
        return experiment, search_space
    else:
        experiment, _, search_space = create_experiment_from_test_case(
            test_id, get_experiment
        )
        return experiment, search_space


class TestDefaultConfiguration:
    @pytest.mark.parametrize("test_id", _test_ids)
    def test_dch_or_tl_creates_default_configuration(
        self,
        test_id,
        get_experiment,
        request,
        get_configurations_2_float,
        get_configurations_float_nom,
        get_configurations_all_types,
    ):
        reset_database()

        experiment, _ = _load_experiment(test_id, get_experiment)
        assert experiment is not None

        has_dch = has_default_config_handler(experiment)
        has_tl = has_transfer_learning(experiment)

        if not has_dch and not has_tl:
            pytest.skip(f"Config {test_id} has neither DCH nor TL enabled")

        default_config = get_default_configuration(experiment)

        assert (
            default_config is not None
        ), f"Failed to create default configuration for: {test_id}"
        assert isinstance(
            default_config, Configuration
        ), f"Default config is not a Configuration instance for: {test_id}"

    @pytest.mark.parametrize("test_id", _test_ids)
    def test_no_dch_means_no_default_config_in_description(
        self,
        test_id,
        get_experiment,
    ):
        reset_database()

        experiment, _ = _load_experiment(test_id, get_experiment)
        assert experiment is not None

        has_dch = has_default_config_handler(experiment)
        has_tl = has_transfer_learning(experiment)

        if has_dch or has_tl:
            pytest.skip(f"Config {test_id} has DCH or TL enabled")

        assert (
            "DefaultConfigurationHandler" not in experiment.description.keys()
        ), f"DCH unexpectedly in description for: {test_id}"
