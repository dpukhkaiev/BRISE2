import logging

from selection.sobol import *


def get_selector(experiment):
    """
    Returns instance of selection algorithm with provided data
    :param experiment: the instance of Experiment class
    """
    logger = logging.getLogger(__name__)
    if experiment.description["SelectionAlgorithm"]["SelectionType"] == "SobolSequence":
        logger.debug("Sobol selection algorithm selected.")
        return SobolSequence(experiment)
    else:
        logger.error("Configuration error - invalid selection algorithm provided: %s." %
                     experiment.description["SelectionAlgorithm"]["SelectionType"])
        raise KeyError("Configuration error - invalid selection algorithm provided: %s." %
                       experiment.description["SelectionAlgorithm"]["SelectionType"])
