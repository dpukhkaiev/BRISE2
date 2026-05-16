import json

from unittest.mock import MagicMock
from repeater.acceptable_error_based import AcceptableErrorBasedType
import pytest

from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from core_entities.search_space import SearchSpace
from repeater.repeater_selector import RepeaterOrchestration
from tools.restore_db import RestoreDB

rdb = RestoreDB()
rdb.restore()

current_experiment = None

@pytest.fixture(autouse=True)
def mock_configurationselection_event_service(monkeypatch):
    """Mock MongoDB, API, and other dependencies for input tests."""
    global current_experiment
    
    # Mock Database & get_last_record_by_experiment_id
    mock_db = MagicMock()
    def mock_get_last_record(collection, experiment_id):
        if current_experiment is None:
            return None
        if collection == "Experiment_description":
            return current_experiment.description
        if collection == "Experiment_state":

            results = {}
            if current_experiment.default_configuration and current_experiment.default_configuration.results:
                results = current_experiment.default_configuration.results

            return {
                "Current_solution": {
                    "Results": results
                },
                "Number_of_measured_configs": 1
            }
        if collection == "Search_space":
            return {"Search_space_size": current_experiment.search_space.size}
        return {}
    
    mock_db.get_last_record_by_experiment_id = mock_get_last_record
   
    # Patch MockDatabase
    monkeypatch.setattr('repeater.repeater_selector.MongoDB', lambda *args, **kwargs: mock_db)
    monkeypatch.setattr('repeater.repeater.MongoDB', lambda *args, **kwargs: mock_db)

    # Add experiment to RepeaterOrchestration after init
    original_init_rep_orc = RepeaterOrchestration.__init__
    def new_init_rep_orc(self, experiment_id: str, experiment=None):
        original_init_rep_orc(self, experiment_id, experiment)
    monkeypatch.setattr('repeater.repeater_selector.RepeaterOrchestration.__init__', new_init_rep_orc)
                        
    # Mock EventService
    mock_connection_instance = MagicMock()
    mock_connection_instance.channel = MagicMock()
    monkeypatch.setattr('repeater.repeater_selector.RepeaterOrchestration._EventServiceConnection', MagicMock(return_value=mock_connection_instance))

    # Add experiment to AcceptableErrorBasedType after init
    original_init_acc_err = AcceptableErrorBasedType.__init__
    def new_init_acc_err(self, experiment_description: dict, experiment_id: str, experiment=None):
        original_init_acc_err(self, experiment_description, experiment_id)
        self.experiment = experiment
    monkeypatch.setattr('repeater.acceptable_error_based.AcceptableErrorBasedType.__init__', new_init_acc_err)

def test_0(get_energy_configurations, get_energy_tasks, get_energy_experiment_and_search_space):
    # New Default Configuration
    configuration, needed_tasks_count = measure_task(get_energy_configurations, get_energy_tasks,
                                                     get_energy_experiment_and_search_space[0], get_energy_experiment_and_search_space[1],
                                                     0, Configuration.Type.DEFAULT,
                                                     {'enabled': True, 'evaluated': False, 'measured': False})

    assert configuration.status == {'enabled': True, 'evaluated': True, 'measured': False}
    assert needed_tasks_count > 0


def test_1(get_energy_configurations, get_energy_tasks, get_energy_experiment_and_search_space):
    # Measured Default Configuration
    configuration, needed_tasks_count = measure_task(get_energy_configurations, get_energy_tasks,
                                                     get_energy_experiment_and_search_space[0], get_energy_experiment_and_search_space[1],
                                                     10, Configuration.Type.DEFAULT,
                                                     {'enabled': True, 'evaluated': True, 'measured': False})

    assert configuration.status == {'enabled': True, 'evaluated': True, 'measured': True}
    assert needed_tasks_count == 0


def test_2(get_energy_configurations, get_energy_tasks, get_energy_experiment_and_search_space):
    # New Predicted Configuration
    configuration, needed_tasks_count = measure_task(get_energy_configurations, get_energy_tasks,
                                                     get_energy_experiment_and_search_space[0], get_energy_experiment_and_search_space[1],
                                                     0, Configuration.Type.PREDICTED,
                                                     {'enabled': True, 'evaluated': False, 'measured': False})

    assert configuration.status == {'enabled': True, 'evaluated': True, 'measured': False}
    assert needed_tasks_count > 0


def test_3(get_energy_configurations, get_energy_tasks, get_energy_experiment_and_search_space):
    # Measured Predicted configuration with low relative error in results.
    configuration, needed_tasks_count = measure_task(get_energy_configurations, get_energy_tasks,
                                                     get_energy_experiment_and_search_space[0], get_energy_experiment_and_search_space[1],
                                                     2, Configuration.Type.PREDICTED,
                                                     {'enabled': True, 'evaluated': True, 'measured': False})

    assert configuration.status == {'enabled': True, 'evaluated': True, 'measured': True}
    assert needed_tasks_count == 0


def test_4(get_energy_configurations, get_energy_tasks, get_energy_experiment_and_search_space):
    # Measured Predicted configuration with high relative error in results.
    configuration, needed_tasks_count = measure_task(get_energy_configurations, get_energy_tasks,
                                                     get_energy_experiment_and_search_space[0], get_energy_experiment_and_search_space[1],
                                                     8, Configuration.Type.PREDICTED,
                                                     {'enabled': True, 'evaluated': True, 'measured': False})

    assert configuration.status == {'enabled': True, 'evaluated': True, 'measured': False}
    assert needed_tasks_count > 0


def test_5(get_energy_configurations, get_energy_tasks, get_energy_experiment_and_search_space):
    # Measured Predicted configuration with number of measured tasks = threshold.
    configuration, needed_tasks_count = measure_task(get_energy_configurations, get_energy_tasks,
                                                     get_energy_experiment_and_search_space[0], get_energy_experiment_and_search_space[1],
                                                     10, Configuration.Type.PREDICTED,
                                                     {'enabled': True, 'evaluated': True, 'measured': False})

    assert configuration.status == {'enabled': True, 'evaluated': True, 'measured': True}
    assert needed_tasks_count == 0


def measure_task(configurations_sample: list, tasks_sample: list, experiment_description: dict,
                 search_space: SearchSpace, measured_tasks: int,
                 config_type: Configuration.Type, config_status: dict):
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

    :return: list of configuration status and number of tasks to measure.
    """
    global current_experiment
    experiment = Experiment(experiment_description, search_space)
    current_experiment = experiment
    Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
    configuration = Configuration(configurations_sample[1]["Params"], config_type, experiment.unique_id)
    configuration.status = config_status
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
    task = json.dumps({"configuration": configuration.to_json()}).encode('utf-8')

    dummy_channel = None
    dummy_method = None
    dummy_properties = None

    results_measurement = orchestrator.measure_configurations(dummy_channel, dummy_method, dummy_properties, task, noDecode=True)

    return results_measurement
