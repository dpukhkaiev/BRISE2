import logging
import os

from tools.mongo_dao import MongoDB
from tools.reflective_class_import import reflective_class_import


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
    logger.debug("Assigned Stop Condition validator.")

    for sc in parameters:
        sc_name = sc["Name"]
        sc_type = sc["Type"]
        if sc["Name"] in experiment_description["StopConditionTriggerLogic"]["Expression"]:
            stop_condition_class = reflective_class_import(class_name=sc["Type"], folder_path="stop_condition")
            stop_condition_class(sc, experiment_description, experiment_id)
            logger.debug(f"Assigned {sc_name} Stop Condition of type {sc_type}.")
        else:
            logger.warning(f"{sc_name} is not used in StopConditionTriggerLogic definition and will be ignored!")
