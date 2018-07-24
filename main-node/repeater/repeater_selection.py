from repeater.default_repeater import DefaultRepeater
from repeater.student_repeater import StudentRepeater


def get_repeater(repeater_type, WS, experiments_configuration):
    if repeater_type == "default":
        return DefaultRepeater(WS, experiments_configuration)
    elif repeater_type == "student_deviation":
        return StudentRepeater(WS, experiments_configuration)
    else:
        raise KeyError