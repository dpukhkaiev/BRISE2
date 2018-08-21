from repeater.repeater_selection import get_repeater
from repeater.default_repeater import DefaultRepeater
from repeater.student_repeater import StudentRepeater
import pytest

WS = "WS"

experiments = {
        "TaskName": "energy_consumption",
        "FileToRead": "Radix-500mio.csv",
        "ResultStructure": ["frequency", "threads", "energy"],
        "ResultDataTypes": ["float", "int", "float"],
        "RepeaterDecisionFunction": "student_deviation",
        "MaxRepeatsOfExperiment": 4
    }

def test_default_repeater():
    repeater_type = "default"
    assert isinstance(get_repeater(repeater_type, WS, experiments), DefaultRepeater)

def test_student_repeater():
    repeater_type = "student_deviation"
    assert isinstance(get_repeater(repeater_type, WS, experiments), StudentRepeater)


def test_KeyError():
    repeater_type = "something"
    with pytest.raises(KeyError):
        get_repeater(repeater_type, WS, experiments)

    repeater_type = 123
    with pytest.raises(KeyError):
        get_repeater(repeater_type, WS, experiments)