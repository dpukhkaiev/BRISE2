import os

os.environ["TEST_MODE"] = "UNIT_TEST"

import pytest
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor

from configuration_selection.configuration_selection import ConfigurationSelection
from configuration_selection.model.surrogate.tree_parzen_estimator import (
    TreeParzenEstimator,
)
from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from test_gen_approach.integration_tests.helpers.config_simulation import setup_default_configuration
from test_gen_approach.integration_tests.helpers.db_utils import reset_database
from test_gen_approach.integration_tests.helpers.experiment_utils import (
    create_configuration_selection,
    create_experiment_from_test_case,
    get_configuration_fixture_name,
    get_objective_count,
    get_parameter_types,
    get_surrogate_type_from_description,
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


class TestSurrogateInstantiation:
    @pytest.mark.parametrize("test_id", _test_ids)
    def test_configuration_selection_creates_successfully(
        self,
        test_id,
        get_experiment,
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
            write_experiment_to_db(experiment, search_space)
            setup_task_configuration(experiment)

        if has_default_config_handler(experiment) or has_transfer_learning(experiment):
            parameter_types = get_parameter_types(experiment)
            fixture_name = get_configuration_fixture_name(parameter_types)
            config_fixture = request.getfixturevalue(fixture_name)
            objective_count = get_objective_count(experiment)

            setup_default_configuration(
                experiment,
                config_fixture,
                objective_count,
                has_transfer_learning(experiment),
            )

        cs = create_configuration_selection(experiment)

        assert (
            cs is not None
        ), f"Failed to create ConfigurationSelection for: {test_id}"
        assert isinstance(
            cs, ConfigurationSelection
        ), f"Expected ConfigurationSelection instance for: {test_id}"

    @pytest.mark.parametrize("test_id", _test_ids)
    def test_configuration_selection_has_predictor(
        self,
        test_id,
        get_experiment,
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
            write_experiment_to_db(experiment, search_space)
            setup_task_configuration(experiment)

        if has_default_config_handler(experiment) or has_transfer_learning(experiment):
            parameter_types = get_parameter_types(experiment)
            fixture_name = get_configuration_fixture_name(parameter_types)
            config_fixture = request.getfixturevalue(fixture_name)
            objective_count = get_objective_count(experiment)
            setup_default_configuration(
                experiment,
                config_fixture,
                objective_count,
                has_transfer_learning(experiment),
            )

        cs = create_configuration_selection(experiment)
        assert cs is not None

        assert hasattr(
            cs, "predictor"
        ), f"ConfigurationSelection missing predictor for: {test_id}"
        assert (
            cs.predictor is not None
        ), f"Predictor is None for: {test_id}"

    @pytest.mark.parametrize("test_id", _test_ids)
    def test_predictor_has_region_model_mapping(
        self,
        test_id,
        get_experiment,
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
            write_experiment_to_db(experiment, search_space)
            setup_task_configuration(experiment)

        if has_default_config_handler(experiment) or has_transfer_learning(experiment):
            parameter_types = get_parameter_types(experiment)
            fixture_name = get_configuration_fixture_name(parameter_types)
            config_fixture = request.getfixturevalue(fixture_name)
            objective_count = get_objective_count(experiment)
            setup_default_configuration(
                experiment,
                config_fixture,
                objective_count,
                has_transfer_learning(experiment),
            )

        cs = create_configuration_selection(experiment)
        assert cs is not None

        assert hasattr(
            cs.predictor, "mapping_region_model"
        ), f"Predictor missing mapping_region_model for: {test_id}"
        assert (
            cs.predictor.mapping_region_model is not None
        ), f"mapping_region_model is None for: {test_id}"
        assert (
            len(cs.predictor.mapping_region_model) > 0
        ), f"mapping_region_model is empty for: {test_id}"

    @pytest.mark.parametrize("test_id", _test_ids)
    def test_surrogate_instance_type_matches_description(
        self,
        test_id,
        get_experiment,
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
            write_experiment_to_db(experiment, search_space)
            setup_task_configuration(experiment)

        if has_default_config_handler(experiment) or has_transfer_learning(experiment):
            parameter_types = get_parameter_types(experiment)
            fixture_name = get_configuration_fixture_name(parameter_types)
            config_fixture = request.getfixturevalue(fixture_name)
            objective_count = get_objective_count(experiment)
            setup_default_configuration(
                experiment,
                config_fixture,
                objective_count,
                has_transfer_learning(experiment),
            )

        cs = create_configuration_selection(experiment)
        assert cs is not None

        surrogate_type_from_desc = get_surrogate_type_from_description(experiment)

        try:
            first_region_model = list(cs.predictor.mapping_region_model.values())[0]
            surrogate_keys = list(first_region_model.mapping_surrogate_objective.keys())

            if len(surrogate_keys) > 0:
                surrogate = surrogate_keys[0]

                if surrogate_type_from_desc == "TreeParzenEstimator":
                    assert isinstance(
                        surrogate, TreeParzenEstimator
                    ), f"Expected TreeParzenEstimator for: {test_id}"

                elif surrogate_type_from_desc == "LinearRegression":
                    assert hasattr(
                        surrogate, "surrogate_instance"
                    ), f"Surrogate missing surrogate_instance for: {test_id}"
                    assert isinstance(
                        surrogate.surrogate_instance, LinearRegression
                    ), f"Expected LinearRegression for: {test_id}"

                elif surrogate_type_from_desc == "GradientBoostingRegressor":
                    assert hasattr(
                        surrogate, "surrogate_instance"
                    ), f"Surrogate missing surrogate_instance for: {test_id}"
                    assert isinstance(
                        surrogate.surrogate_instance, GradientBoostingRegressor
                    ), f"Expected GradientBoostingRegressor for: {test_id}"
                else:
                    assert (
                        surrogate is not None
                    ), f"No surrogate found for: {test_id}"

        except (IndexError, KeyError, AttributeError) as e:
            pytest.fail(f"Error accessing surrogate for {test_id}: {e}")
