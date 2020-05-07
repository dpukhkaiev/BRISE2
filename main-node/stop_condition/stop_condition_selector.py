import logging
import os

from tools.reflective_class_import import reflective_class_import
from tools.mongo_dao import MongoDB


def launch_stop_condition_threads(experiment_id: str):
    """
    :param experiment: the instance of Experiment class
    """
    logger = logging.getLogger(__name__)
    database = MongoDB(os.getenv("BRISE_DATABASE_HOST"), 
                        os.getenv("BRISE_DATABASE_PORT"), 
                        os.getenv("BRISE_DATABASE_NAME"),
                        os.getenv("BRISE_DATABASE_USER"),
                        os.getenv("BRISE_DATABASE_PASS"))

    experiment_description = None
    while experiment_description is None:
        experiment_description = database.get_last_record_by_experiment_id("Experiment_description", experiment_id)

    parameters = experiment_description["StopCondition"]

    stop_condition_validator_class = reflective_class_import(class_name="StopConditionValidator", folder_path="stop_condition")
    stop_condition_validator_class(experiment_id, experiment_description)
    logger.debug(f"Assigned Stop Condition validator.")

    for sc in parameters:
        if sc["Type"] in experiment_description["StopConditionTriggerLogic"]["Expression"]:
            stop_condition_class = reflective_class_import(class_name=sc["Type"], folder_path="stop_condition")
            stop_condition_class(sc, experiment_description, experiment_id)
            msg = sc["Type"]
            logger.debug(f"Assigned {msg} Stop Condition.")
        else:
            msg = sc["Type"]
            logger.warning(f"{msg} is not used in StopConditionTriggerLogic definition and will be ignored!")
