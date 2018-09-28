from repeater.student_repeater import StudentRepeater
from repeater.default_repeater import DefaultRepeater
from repeater.history import History


WS = "should be WS"
EXPERIMENTS = {
    "TaskName": "energy_consumption",
    "FileToRead": "Radix-500mio.csv",
    "ResultStructure": ["frequency", "threads", "energy"],
    "ResultDataTypes": ["float", "int", "float"],
    "RepeaterDecisionFunction": "student_deviation",
    "MaxRepeatsOfExperiment": 4
}


def test_default_student_repeater():
    student_repeater = StudentRepeater(WS, EXPERIMENTS)
    assert isinstance(student_repeater.default_repeater, DefaultRepeater)


def test_decision_function():
    student_repeater = StudentRepeater(WS, EXPERIMENTS)
    test_history = History()
    point = (2900, 32)
    result = student_repeater.decision_function(test_history, point)
    assert result is False  # if test_history is empty

    values = [1, 50]
    test_history.put(point, values[0])
    result = student_repeater.decision_function(test_history, point)
    assert result is False  # if test_history has one element

    # TODO - problem with WSClient
    # test_history.put(point, values[1])
    # result = student_repeater.decision_function(test_history, point)
    # #if test_history has two elements
    # assert result ==

    # TODO - if test_history has more than (equals) "MaxRepeatsOfExperiment": 4 elements (WSClient)
    values = [1, 50, 60, 45, 56]