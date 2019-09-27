import logging
from stop_condition.stop_condition_posterior import StopConditionPosterior
from stop_condition.stop_condition_prior import StopConditionPrior

def get_stop_condition(experiment, is_prior):
    """
    :param experiment: the instance of Experiment class
    :param is_prior: boolean flag, True for priori SC, False for posteriori SC
    :return: Stop Condition object.
    """
    logger = logging.getLogger(__name__)
    parameters = experiment.get_stop_condition_parameters()
    # is_prior added because time-based sc should be activated at the beginning
    # while other sc after model creation
    if is_prior == False:
        stop_condition = StopConditionPosterior(experiment)
        logger.debug("Basic Stop Condition has been created.")
    else:
        stop_condition = StopConditionPrior(experiment)
        logger.debug("Basic Priori Stop Condition has been created.")
    for sc in parameters:
        if is_prior == False:
            if sc["Type"] == "Default":
                from stop_condition.default import DefaultType
                stop_condition = DefaultType(stop_condition, sc["Parameters"])
                logger.debug("Assigned default Stop Condition.")
                continue
            if sc["Type"] == "ImprovementBased":
                from stop_condition.improvement_based import ImprovementBasedType
                stop_condition = ImprovementBasedType(stop_condition, sc["Parameters"])
                logger.debug("Assigned improvement-based Stop Condition.")
                continue
            if sc["Type"] == "Guaranteed":
                from stop_condition.guaranteed import GuaranteedType
                stop_condition = GuaranteedType(stop_condition, sc["Parameters"])
                logger.debug("Assigned guaranteed Stop Condition.")
                continue
            if sc["Type"] == "Adaptive":
                from stop_condition.adaptive import AdaptiveType
                stop_condition = AdaptiveType(stop_condition, sc["Parameters"])
                logger.debug("Assigned adaptive Stop Condition.")
                continue
        else:
            if sc["Type"] == "TimeBased":
                from stop_condition.time_based import TimeBasedType
                stop_condition = TimeBasedType(stop_condition, sc["Parameters"])
                logger.debug("Assigned time-based Stop Condition.")
                continue
    return stop_condition
