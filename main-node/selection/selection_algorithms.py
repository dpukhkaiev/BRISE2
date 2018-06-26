from selection.sobol import *

def get_selector(selector_type, data):
    """
        Returns instance of selection algorithm with provided data
        :param selector_type: - string with name of selection algorithm.
        :param data: list of dimensions that describes a

        """
    if selector_type == "SobolSequence":
        return SobolSequence(data)
    else:
        raise KeyError