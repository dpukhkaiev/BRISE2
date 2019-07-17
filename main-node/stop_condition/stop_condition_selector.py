import logging
from stop_condition.stop_condition import StopCondition

def get_stop_condition(experiment):
    """
    :param experiment: the instance of Experiment class
    :return: Stop Condition object.
    """
    logger = logging.getLogger(__name__)
    parameters = experiment.get_stop_condition_parameters()

    stop_condition = StopCondition(experiment)
    logger.debug("Basic Stop Condition has been created.")
    for sc in parameters:
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

    return stop_condition