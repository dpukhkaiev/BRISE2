import logging

from selection.sobol import *


def get_selector(selection_algorithm_config, search_space):
    """
    Returns instance of selection algorithm with provided data
    :param selection_algorithm_config: - Dict with configuration of selection algorithm.
    :param search_space: list of dimensions for this experiment
                         shape - list of lists, e.g. ``[[1, 2, 4, 8, 16, 32], [1200.0, 1300.0, 2700.0, 2900.0]]``
                                 if there is such search space in "taskData.json" :
                                     {
                                         "threads": [1, 2, 4, 8, 16, 32],
                                         "frequency": [1200.0, 1300.0, 2700.0, 2900.0]
                                     }
    """
    logger = logging.getLogger(__name__)
    if selection_algorithm_config["SelectionType"] == "SobolSequence":
        logger.debug("Sobol selection algorithm selected.")
        return SobolSequence(selection_algorithm_config, search_space)
    else:
        logger.error("Configuration error - invalid selection algorithm provided: %s." %
                     selection_algorithm_config["SelectionType"])
        raise KeyError("Configuration error - invalid selection algorithm provided: %s." %
                     selection_algorithm_config["SelectionType"])
