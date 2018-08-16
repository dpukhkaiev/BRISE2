from repeater.repeater_selection import get_repeater
from repeater.default_repeater import DefaultRepeater
from repeater.student_repeater import StudentRepeater
import pytest

def test_default_repeater():
    WS = "WS"
    repeater_type = "default"
    assert type(get_repeater(repeater_type, WS)) == DefaultRepeater

def test_student_repeater():
    WS = "WS"
    repeater_type = "student_deviation"
    assert type(get_repeater(repeater_type, WS)) == StudentRepeater


def test_KeyError():
    WS = "WS"
    repeater_type = "something"
    with pytest.raises(KeyError):
        get_repeater(repeater_type, WS)
    repeater_type = 123
    with pytest.raises(KeyError):
        get_repeater(repeater_type, WS)