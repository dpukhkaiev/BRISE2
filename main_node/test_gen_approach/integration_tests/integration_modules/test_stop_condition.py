import os

os.environ["TEST_MODE"] = "UNIT_TEST"

import pytest

from stop_condition.stop_condition_selector import launch_stop_condition_threads
from stop_condition.improvement_based import ImprovementBasedType
from stop_condition.quantity_based import QuantityBasedType
from stop_condition.time_based import TimeBased
from stop_condition.validation_based import ValidationBasedType

from core_entities.configuration import Configuration
from core_entities.experiment import Experiment

from test_gen_approach.integration_tests.helpers.experiment_utils import (
    PHASE1_OUTPUT_DIR,
    create_configuration_selection,
    create_experiment_from_test_case,
    get_configuration_fixture_name,
    get_objective_count,
    get_parameter_types,
    instantiate_all_scs,
    load_phase1_config,
    setup_task_configuration,
    write_experiment_to_db,
)
from test_gen_approach.integration_tests.helpers.config_simulation import (
    get_mock_results_for_objectives,
    send_new_configurations,
    setup_default_configuration,
)
from test_gen_approach.integration_tests.helpers.db_utils import reset_database

test_cases_to_check = list(range(15))


_SC_BASE_DESC = {
    "StopCondition": {
        "StopConditionTriggerLogic": {
            "Expression": "sc",
            "InspectionParameters": {
                "RepetitionPeriod": 5,
                "TimeUnit": "seconds",
            },
        }
    }
}


def _run_cs_iterations(experiment, cs, config_fixture, get_workers, objective_count, n=3):
    for i in range(n):
        predicted, _ = send_new_configurations(cs, get_workers)
        if predicted is None or len(predicted) == 0:
            break
        config = predicted[0]
        results = get_mock_results_for_objectives(
            config_fixture, (i + 1) % len(config_fixture), objective_count
        )
        if results is None:
            break
        config.results = results
        config.status["measured"] = True
        config.status["evaluated"] = True
        experiment.measured_configurations.append(config)
        experiment.database.write_one_record(
            "Configuration", config.get_configuration_record()
        )
        experiment.send_state_to_db()


class TestStopConditionIntegration:
    """
    Parametrized over all 15 BRISE test cases.
    """

    @pytest.mark.parametrize("test_case_number", test_cases_to_check)
    def test_sc_instantiation(
        self,
        test_case_number,
        get_experiment,
        get_workers,
        request,
        get_configurations_2_float,
        get_configurations_float_nom,
        get_configurations_all_types,
    ):
        reset_database()

        experiment, _, search_space = create_experiment_from_test_case(
            test_case_number, get_experiment
        )
        assert experiment is not None

        write_experiment_to_db(experiment, search_space)
        setup_task_configuration(experiment)

        parameter_types = get_parameter_types(experiment)
        config_fixture = request.getfixturevalue(
            get_configuration_fixture_name(parameter_types)
        )
        objective_count = get_objective_count(experiment)

        setup_default_configuration(
            experiment, config_fixture, objective_count, is_transfer_learning=False
        )
        experiment.send_state_to_db()

        activated_scs = launch_stop_condition_threads(experiment.unique_id, experiment)
        assert len(activated_scs) >= 1, (
            f"No SCs were activated for test case {test_case_number}"
        )

    @pytest.mark.parametrize("test_case_number", test_cases_to_check)
    def test_sc_decision_is_boolean(
        self,
        test_case_number,
        get_experiment,
        get_workers,
        request,
        get_configurations_2_float,
        get_configurations_float_nom,
        get_configurations_all_types,
    ):
        reset_database()

        experiment, _, search_space = create_experiment_from_test_case(
            test_case_number, get_experiment
        )
        assert experiment is not None

        write_experiment_to_db(experiment, search_space)
        setup_task_configuration(experiment)

        parameter_types = get_parameter_types(experiment)
        config_fixture = request.getfixturevalue(
            get_configuration_fixture_name(parameter_types)
        )
        objective_count = get_objective_count(experiment)

        default_config = setup_default_configuration(
            experiment, config_fixture, objective_count, is_transfer_learning=False
        )
        if default_config is not None:
            experiment.database.update_record(
                "Search_space",
                {"Exp_unique_ID": experiment.unique_id},
                {"Default_configuration": default_config.get_configuration_record()},
            )
        cs = create_configuration_selection(experiment)
        _run_cs_iterations(experiment, cs, config_fixture, get_workers, objective_count)

        activated_scs = launch_stop_condition_threads(experiment.unique_id, experiment)
        assert len(activated_scs) >= 1

        for sc in activated_scs:
            sc.is_finish()
            assert isinstance(sc.decision, bool), (
                f"sc.decision is not bool for test case {test_case_number}: "
                f"got {type(sc.decision)}"
            )


class TestStopConditionTypes:

    @pytest.fixture(autouse=True)
    def setup(self, get_experiment, get_workers, get_configurations_2_float):
        reset_database()

        experiment, _, search_space = create_experiment_from_test_case(
            0, get_experiment
        )
        write_experiment_to_db(experiment, search_space)
        setup_task_configuration(experiment)

        objective_count = get_objective_count(experiment)
        setup_default_configuration(
            experiment,
            get_configurations_2_float,
            objective_count,
            is_transfer_learning=False,
        )
        cs = create_configuration_selection(experiment)
        _run_cs_iterations(
            experiment, cs, get_configurations_2_float, get_workers, objective_count
        )

        self.experiment = experiment
        yield

    def test_quantity_based_not_triggered(self):
        sc_params = {
            "Name": "sc",
            "Type": "quantity_based",
            "Parameters": {"MaxConfigs": 1000},
        }
        sc = QuantityBasedType(sc_params, _SC_BASE_DESC, self.experiment.unique_id)
        sc.is_finish()
        assert isinstance(sc.decision, bool)
        assert sc.decision is False

    def test_quantity_based_triggered(self):
        #QuantityBased: MaxConfigs=1 -> triggered after measuring >= 1 config
        sc_params = {
            "Name": "sc",
            "Type": "quantity_based",
            "Parameters": {"MaxConfigs": 1},
        }
        sc = QuantityBasedType(sc_params, _SC_BASE_DESC, self.experiment.unique_id)
        sc.is_finish()
        assert sc.decision is True

    def test_improvement_based(self):
        # ImprovementBased: large MaxConfigsWithoutImprovement -> decision is bool
        sc_params = {
            "Name": "sc",
            "Type": "improvement_based",
            "Parameters": {"MaxConfigsWithoutImprovement": 100},
        }
        sc = ImprovementBasedType(sc_params, _SC_BASE_DESC, self.experiment.unique_id)
        sc.is_finish()
        assert isinstance(sc.decision, bool)

    def test_validation_based(self):
        sc_params = {"Name": "sc", "Type": "validation_based"}
        sc = ValidationBasedType(sc_params, _SC_BASE_DESC, self.experiment.unique_id)
        sc.is_finish()
        assert isinstance(sc.decision, bool)

    def test_time_based_not_triggered(self):
        # TimeBased: large timeout -> decision stays False right after instantiation
        sc_params = {
            "Name": "sc",
            "Type": "time_based",
            "Parameters": {"MaxRunTime": 3600, "TimeUnit": "seconds"},
        }
        sc = TimeBased(sc_params, _SC_BASE_DESC, self.experiment.unique_id)
        sc.is_finish()
        assert sc.decision is False

    def test_time_based_triggered(self):
        #TimeBased: zero-second timeout -> decision is True on first is_finish() call
        sc_params = {
            "Name": "sc",
            "Type": "time_based",
            "Parameters": {"MaxRunTime": 0, "TimeUnit": "seconds"},
        }
        sc = TimeBased(sc_params, _SC_BASE_DESC, self.experiment.unique_id)
        sc.is_finish()
        assert sc.decision is True



# Phase 1 config tests

_phase1_configs = sorted(f.name for f in PHASE1_OUTPUT_DIR.glob("*.json"))


class TestStopConditionPhase1:

    @pytest.mark.parametrize("config_file", _phase1_configs)
    def test_sc_instantiation(self, config_file, get_configurations_2_float):
        """instantiate_all_scs returns at least one SC for every Phase 1 config."""
        reset_database()

        exp_desc, search_space = load_phase1_config(config_file)
        assert exp_desc is not None
        assert search_space is not None

        experiment = Experiment(exp_desc, search_space)
        Configuration.set_task_config(
            experiment.description["Context"]["TaskConfiguration"]
        )
        write_experiment_to_db(experiment, search_space)
        setup_task_configuration(experiment)

        objective_count = get_objective_count(experiment)
        from test_gen_approach.integration_tests.helpers.config_simulation import setup_default_configuration
        setup_default_configuration(
            experiment, get_configurations_2_float, objective_count, is_transfer_learning=False
        )
        experiment.send_state_to_db()

        scs = instantiate_all_scs(experiment)
        assert len(scs) >= 1, f"No SCs could be instantiated for {config_file}"

    @pytest.mark.parametrize("config_file", _phase1_configs)
    def test_sc_decision_is_boolean(
        self, config_file, get_workers, get_configurations_2_float
    ):
        reset_database()

        exp_desc, search_space = load_phase1_config(config_file)
        assert exp_desc is not None
        assert search_space is not None

        experiment = Experiment(exp_desc, search_space)
        Configuration.set_task_config(
            experiment.description["Context"]["TaskConfiguration"]
        )
        write_experiment_to_db(experiment, search_space)
        setup_task_configuration(experiment)

        objective_count = get_objective_count(experiment)
        from test_gen_approach.integration_tests.helpers.config_simulation import setup_default_configuration
        default_config = setup_default_configuration(
            experiment, get_configurations_2_float, objective_count, is_transfer_learning=False
        )
        if default_config is None:
            pytest.skip(f"Could not initialize default configuration for {config_file}")
        experiment.database.update_record(
            "Search_space",
            {"Exp_unique_ID": experiment.unique_id},
            {"Default_configuration": default_config.get_configuration_record()},
        )
        cs = create_configuration_selection(experiment)
        _run_cs_iterations(experiment, cs, get_configurations_2_float, get_workers, objective_count)

        scs = instantiate_all_scs(experiment)
        assert len(scs) >= 1, f"No SCs could be instantiated for {config_file}"

        for sc in scs:
            sc.is_finish()
            assert isinstance(sc.decision, bool), (
                f"{type(sc).__name__}.decision is not bool in {config_file}"
            )
