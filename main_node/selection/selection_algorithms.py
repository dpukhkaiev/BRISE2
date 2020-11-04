from selection.selection_algorithm_abs import SelectionAlgorithm
from tools.reflective_class_import import reflective_class_import


def get_selector(selection_algorithm: dict) -> SelectionAlgorithm:
    """
    Returns instance of selection algorithm with provided data
    :param selection_algorithm: a description of the chosen selection strategy.
    :return: selector object
    """
    selector_class = reflective_class_import(class_name=selection_algorithm, folder_path="selection")
    return selector_class()
