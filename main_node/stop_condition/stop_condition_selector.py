import logging
import os

from core_entities.experiment import Experiment
from tools.mongo_dao import MongoDB
from tools.reflective_class_import import reflective_class_import

from reconfiguration.effector import Effector

class StopConditionSelector:

    stop_conditions = []
    stop_condition_validator = None

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def launch_stop_condition_threads(self, experiment_id: str, experiment: Experiment = None):
        """
        :param experiment_id: the unique ID of the Experiment
        :param experiment: Experiment class instance, (!)used only in tests
        :return: activated stop condition entities
        """

        self.experiment_id = experiment_id
        
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

        activated_scs = self._create_stop_conditons(experiment_description["StopCondition"])

        return activated_scs

    @Effector.effector("StopCondition")
    def _create_stop_conditons(self, description):
        # Stop old threads
        if StopConditionSelector.stop_condition_validator is not None:
            StopConditionSelector.stop_condition_validator.stop_thread(None, None, None, None)

        for sc in StopConditionSelector.stop_conditions:
            sc.stop_threads(None, None, None, None)
        
        # Create stop condition validator
        stop_condition_validator_class = reflective_class_import(class_name="StopConditionValidator", folder_path="stop_condition")
        StopConditionSelector.stop_condition_validator = stop_condition_validator_class(self.experiment_id, description)
        self.logger.debug("Assigned Stop Condition validator.")

        activated_scs = []
        for sc in description["Instance"]:
            sc_name = description["Instance"][sc]["Name"]
            sc_type = description["Instance"][sc]["Type"]
            if sc_name in description["StopConditionTriggerLogic"]["Expression"]:
                stop_condition_class = reflective_class_import(class_name=sc_type, folder_path="stop_condition")
                temp = stop_condition_class(description["Instance"][sc], description, self.experiment_id)
                activated_scs.append(temp)
                self.logger.debug(f"Assigned {sc_name} Stop Condition of type {sc_type}.")
            else:
                self.logger.warning(f"{sc_name} is not used in StopConditionTriggerLogic definition and will be ignored!")

        StopConditionSelector.stop_conditions = activated_scs
        return activated_scs
    

def launch_stop_condition_threads(experiment_id: str, experiment: Experiment = None):
    """
    Wrapper for creating a class instance and calling the launch_stop_condition_threads method
    :param experiment_id: the unique ID of the Experiment
    :param experiment: Experiment class instance, (!)used only in tests
    :return: activated stop condition entities
    """
    return StopConditionSelector().launch_stop_condition_threads(experiment_id, experiment)