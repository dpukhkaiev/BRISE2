from repeater.repeater_abs import Repeater
from repeater.history import History

EXPERIMENTS = {
        "TaskName": "energy_consumption",
        "FileToRead": "Radix-500mio.csv",
        "ResultStructure": ["frequency", "threads", "energy"],
        "ResultDataTypes": ["float", "int", "float"],
        "RepeaterDecisionFunction": "student_deviation",
        "MaxRepeatsOfExperiment": 4
}
WS = "should be WS"


class MyRepeater(Repeater):
    def decision_function(self, history, point, iterations=10, **configuration):
        all_experiments = history.get(point)
        if len(all_experiments) < iterations:
            return False


def test_default_repeater():
    def_repeater = MyRepeater(WS, EXPERIMENTS)
    assert def_repeater.WSClient == WS
    assert isinstance(def_repeater.history, History)
    assert def_repeater.current_measurement == {}
    assert def_repeater.current_measurement_finished is False
    assert def_repeater.performed_measurements == 0
    assert def_repeater.max_repeats_of_experiment == EXPERIMENTS["MaxRepeatsOfExperiment"]


# TODO - line 47, 78 (repeater_abs.py) there is WSClient
# def test_mesuare_task():
#     WSClient_exp = WSClient()
#     def_Repeater = My_Repeater(WSClient_exp)
#     result_exp = [13000, 1400]
#     task = [(1200, 32), (1900, 2)]
#     io = "io"
#     result = def_Repeater.measure_task(task, io)
#     assert result == result_exp


# TODO - "cast_results" function , WSClient - line 80
# def test_cast_results():