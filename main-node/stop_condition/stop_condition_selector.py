import logging

from tools.reflective_class_import import reflective_class_import
from core_entities.experiment import Experiment

def launch_stop_condition_threads(experiment: Experiment):
    """
    :param experiment: the instance of Experiment class
    """
    logger = logging.getLogger(__name__)
    parameters = experiment.get_stop_condition_parameters()

    stop_condition_validator_class = reflective_class_import(class_name="StopConditionValidator", folder_path="stop_condition")
    stop_condition_validator_class(experiment)
    logger.debug(f"Assigned Stop Condition validator.")

    for sc in parameters:
        if sc["Type"] in experiment.description["StopConditionTriggerLogic"]["Expression"]:
            stop_condition_class = reflective_class_import(class_name=sc["Type"], folder_path="stop_condition")
            stop_condition_class(experiment, sc)
            msg = sc["Type"]
            logger.debug(f"Assigned {msg} Stop Condition.")
        else:
            msg = sc["Type"]
            logger.warning(f"{msg} is not used in StopConditionTriggerLogic definition and will be ignored!")
