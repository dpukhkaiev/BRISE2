import logging


def get_stop_condition(stop_condition_type, minimization_task_bool):
    """
    :param stop_condition_type: String.
            The name of desired decision function for stop_condition.
            Possible values - "default".
            "default" - search for a new point is stopped, if value of solution candidate is better then value of
                        default point.

    :return: Stop Condition object.
    """
    logger = logging.getLogger(__name__)
    if stop_condition_type == "default":
        from stop_condition.stop_condition_default import StopConditionDefault
        logger.info("Default stop condition is selected.")
        return StopConditionDefault(minimization_task_bool)
    else:
        logger.error("Invalid stop condition type is provided!")
        raise KeyError
