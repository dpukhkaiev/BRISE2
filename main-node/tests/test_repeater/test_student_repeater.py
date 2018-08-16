from repeater.student_repeater import StudentRepeater
from repeater.default_repeater import DefaultRepeater
from repeater.history import History

def test_default_student_repeater():
    WS = "WS"
    student_repeater = StudentRepeater(WS)
    assert type(student_repeater.default_repeater) == DefaultRepeater

    #TODO - ??? "super.__init__(*args, **kwargs)"

def test_decision_function():
    WS = "WS"
    student_repeater = StudentRepeater(WS)
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