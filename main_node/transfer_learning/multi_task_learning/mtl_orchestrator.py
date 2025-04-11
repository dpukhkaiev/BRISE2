import logging
from typing import Dict

from tools.reflective_class_import import reflective_class_import
from transfer_learning.multi_task_learning.multi_task_learning_abs import MultiTaskLearning
from transfer_learning.multi_task_learning.base_mtl import BaseMTL


class MultiTaskLearningOrchestrator:
    @staticmethod
    def get_mtl_module(experiment_description: Dict, experiment_id) -> MultiTaskLearning:
        """
        Constructs an instance of a multitask learning module according to the experiment description.
        """
        logger = logging.getLogger(__name__)

        base_mtl = BaseMTL(experiment_description, experiment_id)

        filter_descriptions = list(experiment_description["TransferLearning"]["MultiTaskLearning"]["Filters"].keys())
        for f in filter_descriptions:
            filter_class = (
                reflective_class_import(class_name=experiment_description["TransferLearning"]["MultiTaskLearning"]["Filters"][f]["Type"],
                                        folder_path="transfer_learning/multi_task_learning"))
            base_mtl = filter_class(experiment_description, experiment_id, base_mtl)
            logger.info(f"Assigned {f} multi task learning approach.")

        return base_mtl
