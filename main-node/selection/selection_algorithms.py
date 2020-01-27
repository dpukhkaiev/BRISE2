from selection.sobol import *
from selection.cs_selector import *
from tools.reflective_class_import import reflective_class_import
from core_entities.experiment import Experiment


def get_selector(experiment: Experiment):
    """
    Returns instance of selection algorithm with provided data
    :param experiment: the instance of Experiment class
    :return: selector object
    """
    selector_type = experiment.description["SelectionAlgorithm"]["SelectionType"]
    selector_class = reflective_class_import(class_name=selector_type, folder_path="selection")
    return selector_class(experiment)
