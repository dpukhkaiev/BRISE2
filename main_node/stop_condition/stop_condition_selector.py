import logging
import os

from core_entities.experiment import Experiment
from tools.mongo_dao import MongoDB
from tools.reflective_class_import import reflective_class_import


def launch_stop_condition_threads(experiment_id: str, experiment: Experiment = None):
    """
    :param experiment_id: the unique ID of the Experiment
    :param experiment: Experiment class instance, (!)used only in tests
    :return: activated stop condition entities
    """
    logger = logging.getLogger(__name__)
    if os.environ.get('TEST_MODE') != 'UNIT_TEST':
        database = MongoDB(os.getenv("BRISE_DATABASE_HOST"),
                           os.getenv("BRISE_DATABASE_PORT"),
                           os.getenv("BRISE_DATABASE_NAME"),
                           os.getenv("BRISE_DATABASE_USER"),
                           os.getenv("BRISE_DATABASE_PASS"))

        experiment_description = None
        while experiment_description is None:
            experiment_description = database.get_last_record_by_experiment_id("Experiment_description", experiment_id)
    else:
        database = MongoDB("test", 0, "test", "user", "pass")
        test_experiment = experiment
        experiment_description = test_experiment.description

    parameters = experiment_description["StopCondition"]

    stop_condition_validator_class = reflective_class_import(class_name="StopConditionValidator", folder_path="stop_condition")
    stop_condition_validator_class(experiment_id, experiment_description)
    logger.debug("Assigned Stop Condition validator.")

    activated_scs = []
    for sc in parameters["Instance"]:
        sc_name = parameters["Instance"][sc]["Name"]
        sc_type = parameters["Instance"][sc]["Type"]
        if sc_name in experiment_description["StopCondition"]["StopConditionTriggerLogic"]["Expression"]:
            stop_condition_class = reflective_class_import(class_name=sc_type, folder_path="stop_condition")
            temp = stop_condition_class(parameters["Instance"][sc], experiment_description, experiment_id)
            activated_scs.append(temp)
            logger.debug(f"Assigned {sc_name} Stop Condition of type {sc_type}.")
        else:
            logger.warning(f"{sc_name} is not used in StopConditionTriggerLogic definition and will be ignored!")
    return activated_scs
