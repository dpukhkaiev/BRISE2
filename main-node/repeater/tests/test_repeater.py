from pytest import approx   # default is ± 2.3e-06
from repeater.repeater import Repeater
from WorkerServiceClient.tests.WS_stub import WSClient_Stub
from core_entities.experiment import Experiment
from core_entities.configuration import Configuration
from tools.initial_config import load_experiment_setup


DESCRIPTION_NB, SEARCH_SPACE_NB = load_experiment_setup(exp_desc_file_path="Resources/MLExperiments/NB/NBExperiment.json")
DESCRIPTION_ENERGY, SEARCH_SPACE_ENERGY = load_experiment_setup(exp_desc_file_path="Resources/EnergyExperiment.json")
DESCRIPTION_ENERGY["TaskConfiguration"]["Scenario"]["ws_file"] = "Radix-500mio_avg.csv"
DESCRIPTION_NB["TaskConfiguration"]["Scenario"]["ws_file"] = "NB_final_result.csv"


def measure_task(task_parameters, description, search_space):
    WSClient_exp = WSClient_Stub(description["TaskConfiguration"], 'event_service', 49153, 'TEST_WSClient_results.csv')
    experiment = Experiment(description, search_space)
    Configuration.set_task_config(experiment.description["TaskConfiguration"])
    configuration1 = Configuration(task_parameters[0], Configuration.Type.TEST)
    configuration2 = Configuration(task_parameters[1], Configuration.Type.TEST)
    repeater = Repeater(WSClient_exp, experiment)
    try:
        task = [configuration1, configuration2]

        results_measurement = repeater.measure_configurations(task)
        results_configurations = []
        for key in results_measurement:
            configuration = Configuration.from_json(results_measurement[key]["configuration"])
            results_WO_outliers = repeater.outlier_detectors.find_outliers_for_taskset(
                results_measurement[key]["tasks_results"],
                repeater._result_structure,
                [configuration],
                results_measurement[key]["tasks_to_send"])
            for parameters, task in zip(results_measurement[key]["tasks_to_send"], results_WO_outliers):
                configuration.add_tasks(task)
            results_configurations.append(configuration)

        WSClient_exp.logger.info("Results: %s" % str(WSClient_exp._report_according_to_required_structure()))
        WSClient_exp.dump_results_to_csv()
        return results_configurations
    finally:
        repeater.stop()
        WSClient_exp.stop()



# TODO - must be improve, test function to check WS_stub
def test_measure_task_energy():
    task_parameters = [[1200.0, 32], [1900.0, 2]]
    result_exp = [4357.868, 17449.26]

    result_configurations = measure_task(task_parameters, DESCRIPTION_ENERGY, SEARCH_SPACE_ENERGY)

    assert result_exp[0] == approx(result_configurations[0].get_average_result()[0])
    assert result_exp[1] == approx(result_configurations[1].get_average_result()[0])


def test_measure_task_NB():
    task_parameters = [[True, 'full', 'heuristic', 0.5, None, None, True, 100],
                       [True, 'greedy', None, 10, 0.001, 100, False, None]]
    result_exp = [0.8078, 0.145]

    result_configurations = measure_task(task_parameters, DESCRIPTION_NB, SEARCH_SPACE_NB)

    assert result_exp[0] == approx(result_configurations[0].get_average_result()[0])
    assert result_exp[1] == approx(result_configurations[1].get_average_result()[0])
