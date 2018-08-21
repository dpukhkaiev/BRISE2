from repeater.student_repeater import StudentRepeater
from repeater.default_repeater import DefaultRepeater
from repeater.history import History

def test_default_student_repeater():
    WS = "WS"
    experiments = {
        "TaskName": "energy_consumption",
        "FileToRead": "Radix-500mio.csv",
        "ResultStructure": ["frequency", "threads", "energy"],
        "ResultDataTypes": ["float", "int", "float"],
        "RepeaterDecisionFunction": "student_deviation",
        "MaxRepeatsOfExperiment": 4
    }
    student_repeater = StudentRepeater(WS, experiments)
    assert isinstance(student_repeater.default_repeater, DefaultRepeater)

def test_decision_function():
    WS = "WS"
    experiments = {
        "TaskName": "energy_consumption",
        "FileToRead": "Radix-500mio.csv",
        "ResultStructure": ["frequency", "threads", "energy"],
        "ResultDataTypes": ["float", "int", "float"],
        "RepeaterDecisionFunction": "student_deviation",
        "MaxRepeatsOfExperiment": 4
    }
    student_repeater = StudentRepeater(WS, experiments)
    test_history = History()
    point = (2900, 32)
    result = student_repeater.decision_function(test_history, point)
    # if test_history is empty
    assert result is False

    values = [1, 50]
    test_history.put(point, values[0])
    result = student_repeater.decision_function(test_history, point)
    #if test_history has one element
    assert result is False

    #TODO - problem with WSClient
    # test_history.put(point, values[1])
    # result = student_repeater.decision_function(test_history, point)
    # #if test_history has two elements
    # assert result ==


    #TODO - if test_history has more than (equals) 10 elements