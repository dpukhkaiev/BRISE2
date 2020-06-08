import os
import json

from repeater.repeater_selector import RepeaterOrchestration
from core_entities.experiment import Experiment
from core_entities.configuration import Configuration
from core_entities.search_space import SearchSpace

os.environ["TEST_MODE"] = 'UNIT_TEST'


def test_0(get_sample):
    # New Default Configuration
    configuration, needed_tasks_count = measure_task(get_sample[0], get_sample[1], get_sample[2], get_sample[3], 0, Configuration.Type.DEFAULT, Configuration.Status.NEW)

    assert configuration.status == Configuration.Status.EVALUATED
    assert needed_tasks_count > 0

def test_1(get_sample):
    # Measured Default Configuration
    configuration, needed_tasks_count = measure_task(get_sample[0], get_sample[1], get_sample[2], get_sample[3], 10, Configuration.Type.DEFAULT, Configuration.Status.EVALUATED)

    assert configuration.status == Configuration.Status.MEASURED
    assert needed_tasks_count == 0

def test_2(get_sample):
    # New Predicted Configuration
    configuration, needed_tasks_count = measure_task(get_sample[0], get_sample[1], get_sample[2], get_sample[3], 0, Configuration.Type.PREDICTED, Configuration.Status.NEW)

    assert configuration.status == Configuration.Status.EVALUATED
    assert needed_tasks_count > 0

def test_3(get_sample):
    # Measured Predicted configuration with low relative error in measurings.
    configuration, needed_tasks_count = measure_task(get_sample[0], get_sample[1], get_sample[2], get_sample[3], 2, Configuration.Type.PREDICTED, Configuration.Status.EVALUATED)

    assert configuration.status == Configuration.Status.MEASURED
    assert needed_tasks_count == 0

def test_4(get_sample):
    # Measured Predicted configuration with high relative error in measurings.
    configuration, needed_tasks_count = measure_task(get_sample[0], get_sample[1], get_sample[2], get_sample[3], 8, Configuration.Type.PREDICTED, Configuration.Status.EVALUATED)

    assert configuration.status == Configuration.Status.REPEATED_MEASURING
    assert needed_tasks_count > 0

def test_5(get_sample):
    # Measured Predicted configuration with number of measured tasks = threshold.
    configuration, needed_tasks_count = measure_task(get_sample[0], get_sample[1], get_sample[2], get_sample[3], 10, Configuration.Type.PREDICTED, Configuration.Status.EVALUATED)

    assert configuration.status == Configuration.Status.MEASURED
    assert needed_tasks_count == 0


def measure_task(configurations_sample: list, tasks_sample: list, experiment_description: dict, search_space: SearchSpace, measured_tasks: int, config_type: Configuration.Type, config_status: Configuration.Status):
    """
    Test function for Repeater module.
    Main steps:
    0. Take default tasks sample.
    1. Create instances of Repeater, Experiment, Default Configuration according to test requirements.
    2. Create instance of current measurement.
    3. Call Repeater function. 

    :param configurations_sample: default sample of measured configurations
    :param tasks_sample: default sample of measured tasks
    :param experiment_description: Experiment Description sample in json format
    :param search_space: Search Space sample
    :param measured_tasks: specify number of measured tasks in current measurement.
    :param config_type: specify current measurement configuration type.
    :param config_status: specify current measurement configuration status.

    :return: list of configuration status and number of tasks to measure.
    """
    experiment = Experiment(experiment_description, search_space)
    Configuration.set_task_config(experiment.description["TaskConfiguration"])
    configuration = Configuration(configurations_sample[1]["Params"], config_type)
    configuration.status = config_status
    for i in range(0, measured_tasks):
        configuration.add_tasks(tasks_sample[i])
    orchestrator = RepeaterOrchestration(experiment)
    if config_type == Configuration.Type.DEFAULT:
        orchestrator._type = orchestrator.get_repeater(True)
    else:
        orchestrator._type = orchestrator.get_repeater()
        default_configuration = Configuration(configurations_sample[0]["Params"], Configuration.Type.DEFAULT)
        default_configuration.status = Configuration.Status.MEASURED
        default_configuration._task_amount = configurations_sample[0]["Tasks"]
        default_configuration._average_result = configurations_sample[0]["Avg.result"]
        default_configuration._standard_deviation = configurations_sample[0]["STD"]
        experiment.put_default_configuration(default_configuration)
    task = json.dumps({"configuration": configuration.to_json()})

    dummy_channel = None
    dummy_method = None
    dummy_properties = None

    results_measurement = orchestrator.measure_configurations(dummy_channel, dummy_method, dummy_properties, task)

    return results_measurement
