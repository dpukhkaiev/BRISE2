import logging


def get_stop_condition(is_minimization_experiment, stop_condition_config):
    """
    :param is_minimization_experiment: bool
            Possible values - "True" and "False".
            "True" for the minimization experiment. "False" for the maximization experiment.
    :param stop_condition_config: dict.
            stop_condition_type["StopConditionName"] - String. the name of desired decision function for stop_condition.
            Possible values - "default".
            "default" - The Solution finding stops if the solution candidate's value is not improved more, then
                        'stop_condition_type["ConfigsWithoutImprovement"]' times successively.
            "improved" - The Solution finding stops if the solution candidate's value is not improved more, then
                        'stop_condition_type["ConfigsWithoutImprovement"]' times successively and is better, then
                        the value of default point.
    :return: Stop Condition object.
    """
    logger = logging.getLogger(__name__)
    if stop_condition_config["StopConditionName"] == "default":
        from stop_condition.stop_condition_default import StopConditionDefault
        logger.info("Default stop condition is selected.")
        return StopConditionDefault(is_minimization_experiment=is_minimization_experiment,
                                    stop_condition_config=stop_condition_config)
    elif stop_condition_config["StopConditionName"] == "improved":
        from stop_condition.stop_condition_improved import StopConditionImproved
        logger.info("Improved stop condition is selected.")
        return StopConditionImproved(is_minimization_experiment=is_minimization_experiment,
                                     stop_condition_config=stop_condition_config)
    else:
        logger.error("Invalid stop condition type is provided!")
        raise KeyError("Invalid stop condition name is provided!: %s" % stop_condition_config["StopConditionName"])
