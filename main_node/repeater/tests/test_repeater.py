import json
import os

from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from core_entities.search_space import SearchSpace
from repeater.repeater_selector import RepeaterOrchestration
from tools.restore_db import RestoreDB

rdb = RestoreDB()
rdb.restore()

def test_new_default_configuration_needs_maximal_number_of_tasks(get_energy_configurations, get_energy_tasks, get_energy_experiment_and_search_space):
    # New Default Configuration
    configuration, needed_tasks_count = measure_task(get_energy_configurations, get_energy_tasks,
                                                     get_energy_experiment_and_search_space[0], get_energy_experiment_and_search_space[1],
                                                     0, Configuration.Type.DEFAULT,
                                                     {'enabled': True, 'evaluated': False, 'measured': False})

    assert configuration.status == {'enabled': True, 'evaluated': True, 'measured': False}
    assert needed_tasks_count > 0


def test_default_configuration_measured_after_maximal_number_of_tasks(get_energy_configurations, get_energy_tasks, get_energy_experiment_and_search_space):
    # Measured Default Configuration
    configuration, needed_tasks_count = measure_task(get_energy_configurations, get_energy_tasks,
                                                     get_energy_experiment_and_search_space[0], get_energy_experiment_and_search_space[1],
                                                     10, Configuration.Type.DEFAULT,
                                                     {'enabled': True, 'evaluated': True, 'measured': False})

    assert configuration.status == {'enabled': True, 'evaluated': True, 'measured': True}
    assert needed_tasks_count == 0


def test_new_predicted_configuration_needs_tasks(get_energy_configurations, get_energy_tasks, get_energy_experiment_and_search_space):
    # New Predicted Configuration
    configuration, needed_tasks_count = measure_task(get_energy_configurations, get_energy_tasks,
                                                     get_energy_experiment_and_search_space[0], get_energy_experiment_and_search_space[1],
                                                     0, Configuration.Type.PREDICTED,
                                                     {'enabled': True, 'evaluated': False, 'measured': False})

    assert configuration.status == {'enabled': True, 'evaluated': True, 'measured': False}
    assert needed_tasks_count > 0


def test_no_new_tasks_are_needed_for_accurate_configuration(get_energy_configurations, get_energy_tasks, get_energy_experiment_and_search_space):
    # Measured Predicted configuration with low relative error in results.
    configuration, needed_tasks_count = measure_task(get_energy_configurations, get_energy_tasks,
                                                     get_energy_experiment_and_search_space[0], get_energy_experiment_and_search_space[1],
                                                     2, Configuration.Type.PREDICTED,
                                                     {'enabled': True, 'evaluated': True, 'measured': False})

    assert configuration.status == {'enabled': True, 'evaluated': True, 'measured': True}
    assert needed_tasks_count == 0


def test_new_tasks_are_needed_for_noisy_configuration(get_energy_configurations, get_energy_tasks, get_energy_experiment_and_search_space):
    # Measured Predicted configuration with high relative error in results.
    configuration, needed_tasks_count = measure_task(get_energy_configurations, get_energy_tasks,
                                                     get_energy_experiment_and_search_space[0], get_energy_experiment_and_search_space[1],
                                                     8, Configuration.Type.PREDICTED,
                                                     {'enabled': True, 'evaluated': True, 'measured': False})

    assert configuration.status == {'enabled': True, 'evaluated': True, 'measured': False}
    assert needed_tasks_count > 0


def test_maximal_number_of_tasks_reached(get_energy_configurations, get_energy_tasks, get_energy_experiment_and_search_space):
    # Measured Predicted configuration with number of measured tasks = threshold.
    configuration, needed_tasks_count = measure_task(get_energy_configurations, get_energy_tasks,
                                                     get_energy_experiment_and_search_space[0], get_energy_experiment_and_search_space[1],
                                                     10, Configuration.Type.PREDICTED,
                                                     {'enabled': True, 'evaluated': True, 'measured': False})

    assert configuration.status == {'enabled': True, 'evaluated': True, 'measured': True}
    assert needed_tasks_count == 0


def test_configuration_disabled_after_exceeding_max_failed_tasks(monkeypatch, get_energy_configurations, get_energy_tasks, get_energy_experiment_and_search_space):
    # Configuration that already exhausted MaxFailedTasksPerConfiguration (== 1 for EnergyExperiment) and has
    # no valid tasks.
    published = []
    monkeypatch.setattr(
        "repeater.repeater_selector.publish",
        lambda exchange, routing_key, body: published.append((exchange, routing_key, body))
    )

    configuration, needed_tasks_count = measure_task(get_energy_configurations, get_energy_tasks,
                                                     get_energy_experiment_and_search_space[0], get_energy_experiment_and_search_space[1],
                                                     0, Configuration.Type.PREDICTED,
                                                     {'enabled': True, 'evaluated': False, 'measured': False},
                                                     number_of_failed_tasks=1)

    assert configuration.status == {'enabled': False, 'evaluated': False, 'measured': True}
    assert needed_tasks_count == 0
    assert published == [("experiment_api_exchange", configuration.experiment_id, "increment_bad_configuration_number")]


def measure_task(configurations_sample: list, tasks_sample: list, experiment_description: dict,
                 search_space: SearchSpace, measured_tasks: int,
                 config_type: Configuration.Type, config_status: dict,
                 number_of_failed_tasks: int = 0):
    """
    Test function for Repeater module.
    Main steps:
    0. Take default tasks sample.
    1. Create instances of Repeater, Experiment, Default Configuration according to test requirements.
    2. Create instance of current measurement.
    3. Call Repeater function.

    :param configurations_sample: a sample of measured configurations
    :param tasks_sample: a sample of measured tasks
    :param experiment_description: experiment description in json format
    :param search_space: search space object
    :param measured_tasks: number of already measured tasks in the current configuration.
    :param config_type: current configuration type.
    :param config_status: current configuration status.
    :param number_of_failed_tasks: number of already failed tasks for the current configuration.

    :return: list of configuration status and number of tasks to measure.
    """
    experiment = Experiment(experiment_description, search_space)
    Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
    configuration = Configuration(configurations_sample[1]["Params"], config_type, experiment.unique_id)
    configuration.status = config_status
    configuration.number_of_failed_tasks = number_of_failed_tasks
    for i in range(0, measured_tasks):
        configuration.add_task(tasks_sample[i])
    orchestrator = RepeaterOrchestration(experiment.unique_id, experiment)
    if config_type == Configuration.Type.DEFAULT:
        orchestrator._type = orchestrator.get_repeater(True)
    else:
        orchestrator._type = orchestrator.get_repeater()
        default_configuration = Configuration(
            configurations_sample[0]["Params"], Configuration.Type.DEFAULT, experiment.unique_id
        )
        default_configuration.status = {'enabled': True, 'evaluated': True, 'measured': True}
        default_configuration._task_number = configurations_sample[0]["Tasks"]
        default_configuration.results = configurations_sample[0]["Result"]
        default_configuration._standard_deviation = configurations_sample[0]["STD"]
        experiment.default_configuration = default_configuration
    task = json.dumps({"configuration": configuration.to_json()})

    dummy_channel = None
    dummy_method = None
    dummy_properties = None

    results_measurement = orchestrator.measure_configurations(dummy_channel, dummy_method, dummy_properties, task)

    return results_measurement
