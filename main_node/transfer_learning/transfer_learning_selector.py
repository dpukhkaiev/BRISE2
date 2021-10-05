import logging

from transfer_learning.model_recommendation.decorator import MRBase
from transfer_learning.multi_task_learning.decorator import MTLBase
from tools.reflective_class_import import reflective_class_import


def get_mr_module(experiment_description: dict, experiment_id):
    """
    Constructs instances of model recommendation and multi-task learning according to the experiment description.
    """
    logger = logging.getLogger(__name__)

    model_recommendation = MRBase()
    for key, value in experiment_description["TransferLearning"]["ModelsRecommendation"].items():
        current_mr = reflective_class_import(class_name=key,
                                            folder_path="transfer_learning/model_recommendation")
        model_recommendation = current_mr(model_recommendation, experiment_description)
        logger.info(f"Assigned {key} model recommendation approach.")

    return model_recommendation

def get_mtl_module(experiment_description: dict, experiment_id):
    """
    Constructs instances of model recommendation and multi-task learning according to the experiment description.
    """
    logger = logging.getLogger(__name__)

    multi_task_learning = MTLBase()
    for key, value in experiment_description["TransferLearning"]["MultiTaskLearning"].items():
        current_mtl = reflective_class_import(class_name=key,
                                            folder_path="transfer_learning/multi_task_learning")
        multi_task_learning = current_mtl(multi_task_learning, experiment_description, experiment_id)
        logger.info(f"Assigned {key} multi task learning approach.")

    return multi_task_learning