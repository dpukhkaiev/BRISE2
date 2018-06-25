from selection.sobol import *
def get_selector(selector_type, dimensionality, data):
    if selector_type == "SobolSequence":
        return SobolSequence(dimensionality, data)
    else:
        raise KeyError