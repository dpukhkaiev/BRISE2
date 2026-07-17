import os

os.environ["TEST_MODE"] = "UNIT_TEST"


from test_gen_approach.integration_tests.helpers.config_simulation import add_configuration_to_experiment
from test_gen_approach.integration_tests.helpers.config_simulation import (
    assign_mock_results_to_configuration,
)
from test_gen_approach.integration_tests.helpers.config_simulation import get_mock_results_for_objectives
import pytest
from core_entities.configuration import Configuration
from core_entities.experiment import Experiment

from test_gen_approach.integration_tests.helpers.config_simulation import (
    send_new_configurations,
    setup_default_configuration,
)

from test_gen_approach.integration_tests.helpers.db_utils import reset_database
from test_gen_approach.integration_tests.helpers.experiment_utils import (
    create_configuration_selection,
    create_experiment_from_test_case,
    get_configuration_fixture_name,
    get_objective_count,
    get_parameter_types,
    has_default_config_handler,
    has_transfer_learning,
    load_phase1_config,
    PHASE1_OUTPUT_DIR,
    setup_task_configuration,
    write_experiment_to_db,
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


class TestConfigSelectionLoop:
    @pytest.mark.parametrize("test_id", _test_ids)
    def test_cs_produces_configurations(
        self,
        test_id,
        get_experiment,
        get_workers,
        request,
        get_configurations_2_float,
        get_configurations_float_nom,
        get_configurations_all_types,
    ):
        reset_database()

        experiment, search_space = _load_experiment(test_id, get_experiment)
        # if experiment is None:
        #     pytest.skip(f"Could not load config: {test_id}")
        assert experiment is not None

        is_tl = has_transfer_learning(experiment)

        if is_tl:
            write_experiment_to_db(experiment, search_space)
            setup_task_configuration(experiment)

        parameter_types = get_parameter_types(experiment)
        fixture_name = get_configuration_fixture_name(parameter_types)
        config_fixture = request.getfixturevalue(fixture_name)
        objective_count = get_objective_count(experiment)

        if has_default_config_handler(experiment) or is_tl:
            setup_default_configuration(
                experiment, config_fixture, objective_count, is_tl
            )

        cs = create_configuration_selection(experiment)
        assert cs is not None

        predicted, _ = send_new_configurations(cs, get_workers)

        assert (
            predicted is not None
        ), f"send_new_configurations returned None for: {test_id}"
        assert (
            len(predicted) > 0
        ), f"No configurations have been produced for: {test_id}"

    @pytest.mark.parametrize("test_id", _test_ids)
    def test_predicted_config_is_configuration_instance(
        self,
        test_id,
        get_experiment,
        get_workers,
        request,
        get_configurations_2_float,
        get_configurations_float_nom,
        get_configurations_all_types,
    ):
        reset_database()

        experiment, search_space = _load_experiment(test_id, get_experiment)
        # if experiment is None:
        #     pytest.skip(f"Could not load config: {test_id}")
        assert experiment is not None

        is_tl = has_transfer_learning(experiment)

        if is_tl:
            write_experiment_to_db(experiment, search_space)
            setup_task_configuration(experiment)

        parameter_types = get_parameter_types(experiment)
        fixture_name = get_configuration_fixture_name(parameter_types)
        config_fixture = request.getfixturevalue(fixture_name)
        objective_count = get_objective_count(experiment)

        if has_default_config_handler(experiment) or is_tl:
            setup_default_configuration(
                experiment, config_fixture, objective_count, is_tl
            )

        cs = create_configuration_selection(experiment)
        assert cs is not None

        predicted, _ = send_new_configurations(cs, get_workers)
        assert predicted is not None and len(predicted) > 0

        assert isinstance(
            predicted[0], Configuration
        ), f"New config is not a Configuration instance for: {test_id}"

    @pytest.mark.parametrize("test_id", _test_ids)
    def test_each_iteration_adds_one_config(
        self,
        test_id,
        get_experiment,
        get_workers,
        request,
        get_configurations_2_float,
        get_configurations_float_nom,
        get_configurations_all_types,
    ):
        reset_database()

        experiment, search_space = _load_experiment(test_id, get_experiment)
        # if experiment is None:
        #     pytest.skip(f"Could not load config: {test_id}")
        assert experiment is not None

        is_tl = has_transfer_learning(experiment)

        if is_tl:
            write_experiment_to_db(experiment, search_space)
            setup_task_configuration(experiment)

        parameter_types = get_parameter_types(experiment)
        fixture_name = get_configuration_fixture_name(parameter_types)
        config_fixture = request.getfixturevalue(fixture_name)
        objective_count = get_objective_count(experiment)

        if has_default_config_handler(experiment) or is_tl:
            setup_default_configuration(
                experiment, config_fixture, objective_count, is_tl
            )

        cs = create_configuration_selection(experiment)
        assert cs is not None

        configs = []
        max_iterations = 25
        min_required_iterations = 4

        for i in range(max_iterations):
            predicted, _ = send_new_configurations(cs, get_workers)

            if predicted is None or len(predicted) == 0:
                print(f"{test_id}: stopped at iteration {i} (no more configs)")
                break

            config = predicted[0]

            fixture_index = i % len(config_fixture)
            results = get_mock_results_for_objectives(
                config_fixture, fixture_index, objective_count
            )
            assign_mock_results_to_configuration(config, results, is_tl)
            add_configuration_to_experiment(experiment, config, is_tl)

            configs.append(config)

        assert (
            len(configs) >= min_required_iterations
        ), f"Expected at least {min_required_iterations} configs, got {len(configs)} for: {test_id}"

        print(f"{test_id}: completed {len(configs)} iterations")

    @pytest.mark.parametrize("test_id", _test_ids)
    def test_non_tl_uses_correct_config_types(
        self,
        test_id,
        get_experiment,
        get_workers,
        request,
        get_configurations_2_float,
        get_configurations_float_nom,
        get_configurations_all_types,
    ):
        reset_database()

        experiment, search_space = _load_experiment(test_id, get_experiment)
        # if experiment is None:
        #     pytest.skip(f"Could not load config: {test_id}")
        assert experiment is not None

        if has_transfer_learning(experiment):
            pytest.skip(f"Config {test_id} is a TL experiment")

        parameter_types = get_parameter_types(experiment)
        fixture_name = get_configuration_fixture_name(parameter_types)
        config_fixture = request.getfixturevalue(fixture_name)
        objective_count = get_objective_count(experiment)

        if has_default_config_handler(experiment):
            setup_default_configuration(
                experiment, config_fixture, objective_count, is_transfer_learning=False
            )

        cs = create_configuration_selection(experiment)
        assert cs is not None

        valid_types = [Configuration.Type.FROM_SELECTOR, Configuration.Type.PREDICTED]

        for i in range(5):
            predicted, _ = send_new_configurations(cs, get_workers)
            if predicted and len(predicted) > 0:
                config = predicted[0]

                assert (
                    config.type in valid_types
                ), f"Non-TL config type {config.type} not valid at iteration {i} for: {test_id}"

                results = get_mock_results_for_objectives(
                    config_fixture, i, objective_count
                )
                assign_mock_results_to_configuration(
                    config, results, is_transfer_learning=False
                )
                add_configuration_to_experiment(
                    experiment, config, is_transfer_learning=False
                )
