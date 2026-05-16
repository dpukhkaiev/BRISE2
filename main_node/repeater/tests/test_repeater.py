import json
from tools.mongo_dao import MongoDB

from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from core_entities.search_space import SearchSpace
from repeater.repeater_selector import RepeaterOrchestration

def test_0(replace_db, get_energy_configurations, get_energy_tasks, get_energy_experiment_and_search_space):
    # New Default Configuration
    configuration, needed_tasks_count = measure_task(replace_db, get_energy_configurations, get_energy_tasks,
                                                     get_energy_experiment_and_search_space[0], get_energy_experiment_and_search_space[1],
                                                     0, Configuration.Type.DEFAULT,
                                                     {'enabled': True, 'evaluated': False, 'measured': False})

    assert configuration.status == {'enabled': True, 'evaluated': True, 'measured': False}
    assert needed_tasks_count > 0


def test_1(replace_db, get_energy_configurations, get_energy_tasks, get_energy_experiment_and_search_space):
    # Measured Default Configuration
    configuration, needed_tasks_count = measure_task(replace_db, get_energy_configurations, get_energy_tasks,
                                                     get_energy_experiment_and_search_space[0], get_energy_experiment_and_search_space[1],
                                                     10, Configuration.Type.DEFAULT,
                                                     {'enabled': True, 'evaluated': True, 'measured': False})

    assert configuration.status == {'enabled': True, 'evaluated': True, 'measured': True}
    assert needed_tasks_count == 0


def test_2(replace_db, get_energy_configurations, get_energy_tasks, get_energy_experiment_and_search_space):
    # New Predicted Configuration
    configuration, needed_tasks_count = measure_task(replace_db, get_energy_configurations, get_energy_tasks,
                                                     get_energy_experiment_and_search_space[0], get_energy_experiment_and_search_space[1],
                                                     0, Configuration.Type.PREDICTED,
                                                     {'enabled': True, 'evaluated': False, 'measured': False})

    assert configuration.status == {'enabled': True, 'evaluated': True, 'measured': False}
    assert needed_tasks_count > 0


def test_3(replace_db, get_energy_configurations, get_energy_tasks, get_energy_experiment_and_search_space):
    # Measured Predicted configuration with low relative error in results.
    configuration, needed_tasks_count = measure_task(replace_db, get_energy_configurations, get_energy_tasks,
                                                     get_energy_experiment_and_search_space[0], get_energy_experiment_and_search_space[1],
                                                     2, Configuration.Type.PREDICTED,
                                                     {'enabled': True, 'evaluated': True, 'measured': False})

    assert configuration.status == {'enabled': True, 'evaluated': True, 'measured': True}
    assert needed_tasks_count == 0


def test_4(replace_db, get_energy_configurations, get_energy_tasks, get_energy_experiment_and_search_space):
    # Measured Predicted configuration with high relative error in results.
    configuration, needed_tasks_count = measure_task(replace_db, get_energy_configurations, get_energy_tasks,
                                                     get_energy_experiment_and_search_space[0], get_energy_experiment_and_search_space[1],
                                                     8, Configuration.Type.PREDICTED,
                                                     {'enabled': True, 'evaluated': True, 'measured': False})

    assert configuration.status == {'enabled': True, 'evaluated': True, 'measured': False}
    assert needed_tasks_count > 0


def test_5(replace_db, get_energy_configurations, get_energy_tasks, get_energy_experiment_and_search_space):
    # Measured Predicted configuration with number of measured tasks = threshold.
    configuration, needed_tasks_count = measure_task(replace_db, get_energy_configurations, get_energy_tasks,
                                                     get_energy_experiment_and_search_space[0], get_energy_experiment_and_search_space[1],
                                                     10, Configuration.Type.PREDICTED,
                                                     {'enabled': True, 'evaluated': True, 'measured': False})

    assert configuration.status == {'enabled': True, 'evaluated': True, 'measured': True}
    assert needed_tasks_count == 0

def seed_test_experiment(db_client: MongoDB, experiment: Experiment):
    """Insert the test experiments into the database"""
    db_client.write_one_record("Experiment_description", experiment.get_experiment_description_record())
    
def measure_task(db_client: MongoDB, configurations_sample: list, tasks_sample: list, experiment_description: dict,
                 search_space: SearchSpace, measured_tasks: int,
                 config_type: Configuration.Type, config_status: dict):
    """
    Test function for Repeater module.
    Main steps:
    0. Take default tasks sample.
    1. Create instances of Repeater, Experiment, Default Configuration according to test requirements.
    2. Create instance of current measurement.
    3. Call Repeater function.

    :param db_client: the test Database client
    :param configurations_sample: a sample of measured configurations
    :param tasks_sample: a sample of measured tasks
    :param experiment_description: experiment description in json format
    :param search_space: search space object
    :param measured_tasks: number of already measured tasks in the current configuration.
    :param config_type: current configuration type.
    :param config_status: current configuration status.

    :return: list of configuration status and number of tasks to measure.
    """
    global current_experiment
    experiment = Experiment(experiment_description, search_space)
    seed_test_experiment(db_client, experiment)

    Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
    configuration = Configuration(configurations_sample[1]["Params"], config_type, experiment.unique_id)
    configuration.status = config_status
    for i in range(0, measured_tasks):
        configuration.add_task(tasks_sample[i])
    orchestrator = RepeaterOrchestration(experiment.unique_id)
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
    task = json.dumps({"configuration": configuration.to_json()}).encode('utf-8')

    dummy_channel = None
    dummy_method = None
    dummy_properties = None

    results_measurement = orchestrator.measure_configurations(dummy_channel, dummy_method, dummy_properties, task, noDecode=True)

    return results_measurement
