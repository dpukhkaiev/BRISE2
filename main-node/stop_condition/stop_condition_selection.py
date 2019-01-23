import logging


def get_stop_condition(experiment):
    """
    :param experiment: the instance of Experiment class
    :return: Stop Condition object.
    """
    logger = logging.getLogger(__name__)

    # is_minimization_experiment: bool
    # Possible values - "True" and "False".
    # "True" for the minimization experiment. "False" for the maximization experiment.

    is_minimization_experiment = experiment.description["ModelConfiguration"]["isMinimizationExperiment"]

    # stop_condition_config: dict.
    #                        key - string, stop condition type.
    #                        value - dict, specific stop condition config depending on stop condition type.

    # Possible values of key- "default", "improvement_based", "adaptive".
    # "default" - The Solution finding stops if the solution candidate's value is not improved more, then
    #             'stop_condition_type["MaxConfigsWithoutImprovement"]' times successively.
    # "improvement_based" - The Solution finding stops if the solution candidate's value is not improved more,
    #                       then 'stop_condition_type["MaxConfigsWithoutImprovement"]' times successively and is
    #                       better, then the value of default point.
    # "adaptive" - The Solution finding stops if the solution candidate's value is not improved more, then
    #              "N" times successively. "N" is calculated as part of full search space size.
    #              The part is determined by configs's value - "SearchSpacePercentageWithoutImprovement".
    stop_condition_config = experiment.description["StopCondition"]

    stop_condition_config_specific = {}
    stop_condition_type = ""

    for key, value in stop_condition_config.items():
        stop_condition_type = key
        stop_condition_config_specific = value

    if stop_condition_type == "default":
        from stop_condition.stop_condition_default import StopConditionDefault
        logger.info("Default stop condition is selected.")
        return StopConditionDefault(is_minimization_experiment=is_minimization_experiment,
                                    stop_condition_config=stop_condition_config_specific)
    elif stop_condition_type == "improvement_based":
        from stop_condition.stop_condition_improvement_based import StopConditionImprovementBased
        logger.info("Improved stop condition is selected.")
        return StopConditionImprovementBased(is_minimization_experiment=is_minimization_experiment,
                                             stop_condition_config=stop_condition_config_specific)
    elif stop_condition_type == "adaptive":
        from stop_condition.stop_condition_adaptive import StopConditionAdaptive
        logger.info("Adaptive stop condition is selected.")
        return StopConditionAdaptive(is_minimization_experiment=is_minimization_experiment,
                                     stop_condition_config=stop_condition_config_specific,
                                     search_space_size=len(experiment.search_space))
    else:
        logger.error("Invalid stop condition type is provided!")
        raise KeyError("Invalid stop condition name is provided!: %s" % stop_condition_config["StopConditionName"])
