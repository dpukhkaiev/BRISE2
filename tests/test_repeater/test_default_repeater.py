from repeater.default_repeater import DefaultRepeater
from repeater.history import History

EXPERIMENTS = {
        "TaskName": "energy_consumption",
        "FileToRead": "Radix-500mio.csv",
        "ResultStructure": ["frequency", "threads", "energy"],
        "ResultDataTypes": ["float", "int", "float"],
        "Type": "student_deviation",
        "MaxTasksPerConfiguration": 4
}
WS = "should be WS"


def test_decision_function_empty_history():
    def_repeater = DefaultRepeater(WS, EXPERIMENTS)
    result = def_repeater.decision_function(def_repeater.history, (1200, 32)) #history is empty
    assert result is False


# TODO - make history with 10+ elements (WSClient)
def test_decision_function():
    point = (2400, 2)
    values = [45, 68, 56, 78, 44, 908, 100, 406]
    history1 = History()
    for v in values:
        history1.put(point, v)

    def_repeater = DefaultRepeater(WS, EXPERIMENTS)
    result = def_repeater.decision_function(history1, point)
