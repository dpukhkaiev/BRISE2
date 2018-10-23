import logging


def get_stop_condition(stop_condition_type):
    """
    :param stop_condition_type: String.
            The name of desired decision function for stop_condition.
            Possible values - "default".
            "default" - ... TODO.

    :return: Stop Condition object.
    """
    logger = logging.getLogger(__name__)
    if stop_condition_type == "default":
        from stop_condition.stop_condition_bo import StopConditionBO
        logger.info("Default stop condition is selected.")
        return StopConditionBO()
    else:
        logger.error("Invalid stop condition type is provided!")
        raise KeyError
