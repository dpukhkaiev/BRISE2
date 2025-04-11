import logging

from tools.reflective_class_import import reflective_class_import


class MetricOrchestrator:
    def get_metric(self, metric_description: dict, is_mimimization: bool):
        """
        Construct instance of metric according to the experiment description.
        """
        logger = logging.getLogger(__name__)
        metric = list(metric_description.keys())[0]
        current_mr = reflective_class_import(class_name=metric,
                                             folder_path="transfer_learning/model_recommendation/metrics")
        metric_class = current_mr(is_mimimization)
        logger.info(f"Assigned {metric} metric.")

        return metric_class
