import types
import logging

from repeater.default_repeater import DefaultRepeater
from repeater.student_repeater import StudentRepeater


def get_repeater(repeater_type, WS, whole_task_config):
    """

    :param repeater_type: String.
            The name of desired decision function for repeater.
            Possible values - "default", "student_deviation".
            "default" - repeats each task fixed number of times, no evaluation performed.
            "student_deviation" - repeats each task until results for these task reach appropriate accuracy,
                the quality of each configuration (better configuration - better quality) and deviation of each
                experiment are taken into account.
    :param WS: WorkerService client object.
    :param whole_task_config: Dict.
            Dictionary object representing task configuration file.
    :return: Repeater object.
    """
    logger = logging.getLogger(__name__)
    if repeater_type == "default":
        return DefaultRepeater(WS, whole_task_config)
    elif repeater_type == "student_deviation":
        return StudentRepeater(WS, whole_task_config)
    else:
        logger.error("Invalid repeater type provided!")
        raise KeyError("Invalid repeater type provided!")

def change_decision_function(repeater, repeater_type):
    """
        This method change current decision function of repeater at runtime.
    :param repeater_type: String.
            The name of desired decision function for repeater.
            Possible values - "default", "student_deviation".
            "default" - repeats each task fixed number of times, no evaluation performed.
            "student_deviation" - repeats each task until results for these task reach appropriate accuracy,
                the quality of each configuration (better configuration - better quality) and deviation of each
                experiment are taken into account.
    :return: Repeater object.
    """
    logger = logging.getLogger(__name__)
    if repeater_type == "default":
        repeater.decision_function = types.MethodType(DefaultRepeater.decision_function, repeater)
        return repeater
    elif repeater_type == "student_deviation":
        repeater.decision_function = types.MethodType(StudentRepeater.decision_function, repeater)
        return repeater
    else:
        logger.error("Invalid repeater type provided!")
        raise KeyError("Invalid repeater type provided!")
