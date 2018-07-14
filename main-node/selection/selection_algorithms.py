from selection.sobol import *

def get_selector(selection_algorithm_config, search_space):
    """
        Returns instance of selection algorithm with provided data
        :param selection_algorithm_config: - Dict with configuration of selection algorithm.
        :param search_space: list of dimensions for this experiment

        """
    if selection_algorithm_config["SelectionType"] == "SobolSequence":
        return SobolSequence(selection_algorithm_config, search_space)
    else:
        print("ERROR: Configuration error - not valid selection algorithm.")
        raise KeyError