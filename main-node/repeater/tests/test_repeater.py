from pytest import approx   # default is ± 2.3e-06
from repeater.repeater import Repeater
from WorkerServiceClient.tests.WS_stub import WSClient_Stub
from core_entities.experiment import Experiment
from core_entities.configuration import Configuration

DESCRIPTION_NB = {
    "TaskConfiguration":{
        "TaskName"          : "taskNB",
        "WorkerConfiguration":{
            "ws_file": "taskNB1.csv"
        },
        "TaskParameters"   : ["laplace_correction", "estimation_mode", "bandwidth_selection", "bandwidth", "minimum_bandwidth", "number_of_kernels", "use_application_grid", "application_grid_size"],
        "ResultStructure"   : ["PREC_AT_99_REC"],
        "ResultDataTypes"  : ["float"],
        "MaxTimeToRunTask": 10
    },
    "Repeater":{
        "Type": "student_deviation",
        "Parameters": {
            "MaxTasksPerConfiguration": 10,
            "MinTasksPerConfiguration": 2,
            "BaseAcceptableErrors": [5],
            "ConfidenceLevels": [0.95],
            "DevicesScaleAccuracies": [0],
            "DevicesAccuracyClasses": [0],
            "ModelAwareness": {
                "isEnabled": True,
                "MaxAcceptableErrors": [50],
                "RatiosMax": [10]
            }
        }
    }
}

DESCRIPTION_ENERGY = {
    "TaskConfiguration":{
        "TaskName"          : "energy_consumption",
        "WorkerConfiguration":{
            "ws_file": "Radix-500mio_avg.csv"
        },
        "TaskParameters"   : ["frequency", "threads"],
        "ResultStructure"   : ["energy"],
        "ResultDataTypes"  : ["float"],
        "MaxTimeToRunTask": 10
    },
    "Repeater":{
        "Type": "student_deviation",
        "Parameters": {
            "MaxTasksPerConfiguration": 10,
            "MinTasksPerConfiguration": 2,
            "BaseAcceptableErrors": [5],
            "ConfidenceLevels": [0.95],
            "DevicesScaleAccuracies": [0],
            "DevicesAccuracyClasses": [0],
            "ModelAwareness": {
                "isEnabled": True,
                "MaxAcceptableErrors": [50],
                "RatiosMax": [10]
            }
        }
    }
}
# class MyRepeater(Repeater):
#     def decision_function(self, history, point, iterations=10, **configuration):
#         all_experiments = history.get(point)
#         if len(all_experiments) < iterations:
#             return False
#
#
# def test_default_repeater():
#     def_repeater = MyRepeater(WS, EXPERIMENTS)
#     assert def_repeater.WSClient == WS
#     assert isinstance(def_repeater.history, History)
#     assert def_repeater.current_measurement == {}
#     assert def_repeater.current_measurement_finished is False
#     assert def_repeater.performed_measurements == 0
#     assert def_repeater.max_repeats_of_experiment == EXPERIMENTS["MaxTasksPerConfiguration"]


def measure_task(task_parameters, description):
    WSClient_exp = WSClient_Stub(description["TaskConfiguration"], 'Stub', 'TEST_WSClient_results.csv')
    experiment = Experiment(description)
    Configuration.set_task_config(experiment.description["TaskConfiguration"])
    configuration1 = Configuration(task_parameters[0])
    configuration2 = Configuration(task_parameters[1])
    repeater = Repeater(WSClient_exp, experiment)

    task = [configuration1, configuration2]

    result_configurations = repeater.measure_configurations(task, experiment)

    return result_configurations


# TODO - must be improve, test function to check WS_stub
def test_measure_task_energy():
    task_parameters = [[1200.0, 32], [1900.0, 2]]
    result_exp = [4357.868, 17449.26]

    result_configurations = measure_task(task_parameters, DESCRIPTION_ENERGY)

    assert result_exp[0] == approx(result_configurations[0].get_average_result()[0])
    assert result_exp[1] == approx(result_configurations[1].get_average_result()[0])


def test_measure_task_NB():
    task_parameters = [[True, 'full', 'fix', 1, 0.001, 100, False, 1000],
                       [True, 'full', 'fix', 0.5, 5, 1000, False, 1000]]
    result_exp = [0.1179, 0.1818]

    result_configurations = measure_task(task_parameters, DESCRIPTION_NB)

    assert result_exp[0] == approx(result_configurations[0].get_average_result()[0])
    assert result_exp[1] == approx(result_configurations[1].get_average_result()[0])

