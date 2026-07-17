from traceback import print_stack
from configuration_selection.configuration_selection import (
    ConfigurationSelection,
)
from default_config_handler.default_configuration_handler_orchestrator import (
    DefaultConfigHandlerOrchestrator,
)
from core_entities.configuration import Configuration
from core_entities.experiment import Experiment


def setup_default_configuration(
    experiment: Experiment,
    config_fixture,
    objective_count: int,
    is_transfer_learning: bool,
):
    try:
        dch_o = DefaultConfigHandlerOrchestrator()
        default_config_handler = dch_o.get_default_configuration_handler(
            experiment=experiment
        )
        default_configuration = default_config_handler.get_default_configuration()

        fixture_index = 9 if objective_count == 1 else 10
        results = get_mock_results_for_objectives(
            config_fixture, fixture_index, objective_count
        )

        if results is not None:
            default_configuration.results = results

        default_configuration.status["measured"] = True
        default_configuration.status["evaluated"] = True
        experiment.default_configuration = default_configuration

        if not is_transfer_learning:
            experiment.evaluated_configurations.append(default_configuration)
            experiment.measured_configurations.append(default_configuration)

        return default_configuration
    except Exception as e:
        print(f"Failed to setup default configuration: {e}")
        print_stack()
        return None


def get_mock_results_for_objectives(config_fixture, index: int, objective_count: int):
    try:
        if index >= len(config_fixture):
            print(
                f"Index {index} out of range for config_fixture (len={len(config_fixture)})"
            )
            return None

        base_results = config_fixture[index]["Result"]

        if objective_count == 1:
            return {"Y1": base_results["Y1"]}
        elif objective_count == 2:
            return {k: v for k, v in base_results.items() if k in ["Y1", "Y2"]}
        elif objective_count == 5:
            return dict(base_results)
    except (KeyError, TypeError, IndexError) as e:
        print(f"Failed to get mock results: {e}")
        return None


def assign_mock_results_to_configuration(
    configuration: Configuration,
    results,
    is_transfer_learning: bool = False,
):
    try:
        configuration.results = results
        configuration.status["measured"] = True
        configuration.status["evaluated"] = True

        if is_transfer_learning:
            configuration.status["enabled"] = True

        return True
    except Exception as e:
        print(f"Failed to assign results to configuration: {e}")
        print_stack()
        return False


def add_configuration_to_experiment(
    experiment: Experiment,
    configuration: Configuration,
    is_transfer_learning: bool = False,
):
    try:
        if is_transfer_learning:
            experiment.add_configuration(configuration)
            experiment.database.write_one_record(
                "Configuration", configuration.get_configuration_record()
            )
            experiment.send_state_to_db()
        else:
            experiment.measured_configurations.append(configuration)

        return True
    except Exception as e:
        print(f"Failed to add configuration to experiment: {e}")
        print_stack()
        return False


def send_new_configurations(cs: ConfigurationSelection, get_workers_fixture):
    try:
        predicted, measured = cs.send_new_configurations_to_measure(
            "", "", "", get_workers_fixture
        )
        return predicted, measured
    except Exception as e:
        print(f"Failed to send new configurations: {e}")
        print_stack()
        return None, None
