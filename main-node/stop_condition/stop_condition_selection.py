import logging


def get_stop_condition(is_minimization_experiment, stop_condition_config, search_space_size):
    """
    :param is_minimization_experiment: bool
            Possible values - "True" and "False".
            "True" for the minimization experiment. "False" for the maximization experiment.
    :param stop_condition_config: dict.
            stop_condition_type["StopConditionName"] - String. the name of desired decision function for stop_condition.
            Possible values - "default".
            "default" - The Solution finding stops if the solution candidate's value is not improved more, then
                        'stop_condition_type["MaxConfigsWithoutImprovement"]' times successively.
            "improvement_based" - The Solution finding stops if the solution candidate's value is not improved more,
                                  then 'stop_condition_type["MaxConfigsWithoutImprovement"]' times successively and is
                                  better, then the value of default point.
            "adaptive" - The Solution finding stops if the solution candidate's value is not improved more, then
                         "N" times successively. "N" is calculated as part of full search space size.
                         The part is determined by configs's value - "SearchSpacePercentageWithoutImprovement".
    :param search_space_size: int
    :return: Stop Condition object.
    """
    logger = logging.getLogger(__name__)
    if stop_condition_config["StopConditionName"] == "default":
        from stop_condition.stop_condition_default import StopConditionDefault
        logger.info("Default stop condition is selected.")
        return StopConditionDefault(is_minimization_experiment=is_minimization_experiment,
                                    stop_condition_config=stop_condition_config)
    elif stop_condition_config["StopConditionName"] == "improvement_based":
        from stop_condition.stop_condition_improvement_based import StopConditionImprovementBased
        logger.info("Improved stop condition is selected.")
        return StopConditionImprovementBased(is_minimization_experiment=is_minimization_experiment,
                                             stop_condition_config=stop_condition_config)
    elif stop_condition_config["StopConditionName"] == "adaptive":
        from stop_condition.stop_condition_adaptive import StopConditionAdaptive
        logger.info("Adaptive stop condition is selected.")
        return StopConditionAdaptive(is_minimization_experiment=is_minimization_experiment,
                                     stop_condition_config=stop_condition_config,
                                     search_space_size=search_space_size)
    else:
        logger.error("Invalid stop condition type is provided!")
        raise KeyError("Invalid stop condition name is provided!: %s" % stop_condition_config["StopConditionName"])
