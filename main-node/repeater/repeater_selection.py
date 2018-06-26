from repeater.default_repeater import DefaultRepeater
from repeater.student_repeater import StudentRepeater
def get_repeater(repeater_type, WS):
    if repeater_type == "default":
        return  DefaultRepeater(WS)
    elif repeater_type == "student_deviation":
        return StudentRepeater(WS)
    else:
        raise KeyError