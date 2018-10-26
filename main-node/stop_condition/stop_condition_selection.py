import logging


def get_stop_condition(stop_condition_type, minimization_task_bool, default_value=None):
    """
    :param stop_condition_type: String.
            The name of desired decision function for stop_condition.
            Possible values - "default".
            "default" - Search for a new point is stopped, if the value of solution candidate is better, then the value
                        of default point.

    :return: Stop Condition object.
    """
    logger = logging.getLogger(__name__)
    if stop_condition_type == "default":
        from stop_condition.stop_condition_default import StopConditionDefault
        logger.info("Default stop condition is selected.")
        return StopConditionDefault(minimization_task_bool=minimization_task_bool,
                                    default_value=default_value)
    else:
        logger.error("Invalid stop condition type is provided!")
        raise KeyError
