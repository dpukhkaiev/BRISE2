import logging
from typing import Dict
from tools.reflective_class_import import reflective_class_import
from transfer_learning.transfer_expediency_determination.transfer_expediency_analyser import TransferExpediencyAnalyser


class TEDOrchestrator:

    @staticmethod
    def get_ted_module(ted_description: Dict, experiment_id) -> TransferExpediencyAnalyser:
        """
        Constructs an instance of transfer expediency determination module according to the experiment description.
        """
        logger = logging.getLogger(__name__)

        keys = list(ted_description.keys())
        assert len(keys) == 1
        feature_name = keys[0]

        ted_class = reflective_class_import(class_name=ted_description[feature_name]["Type"],
                                            folder_path="transfer_learning/transfer_expediency_determination")
        ted = ted_class(ted_description, experiment_id)
        logger.info(f"Assigned {feature_name} expediency determination approach.")

        return ted
