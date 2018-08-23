from repeater.repeater_abs import Repeater
from repeater.history import History

experiments = {
        "TaskName": "energy_consumption",
        "FileToRead": "Radix-500mio.csv",
        "ResultStructure": ["frequency", "threads", "energy"],
        "ResultDataTypes": ["float", "int", "float"],
        "RepeaterDecisionFunction": "student_deviation",
        "MaxRepeatsOfExperiment": 4
    }

class My_Repeater(Repeater):
    def decision_function(self, history, point, iterations=10, **configuration):
        all_experiments = history.get(point)
        if len(all_experiments) < iterations:
            return False

def test_default_Repeater():
    WSClient_exp = "WS"
    def_Repeater = My_Repeater(WSClient_exp, experiments)
    assert def_Repeater.WSClient == WSClient_exp
    assert isinstance(def_Repeater.history, History)
    assert def_Repeater.current_measurement == {}
    assert def_Repeater.current_measurement_finished is False
    assert def_Repeater.performed_measurements == 0

# TODO - ??? test abstract method "decision_function"

# TODO - line 46, 78 (repeater_abs.py) there is WSClient

# def test_mesuare_task():
#     WSClient_exp = WSClient()
#     def_Repeater = My_Repeater(WSClient_exp)
#     result_exp = [13000, 1400]
#     task = [(1200, 32), (1900, 2)]
#     io = "io"
#     result = def_Repeater.measure_task(task, io)
#     assert result == result_exp