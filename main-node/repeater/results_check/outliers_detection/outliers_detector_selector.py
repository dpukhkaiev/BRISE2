import logging

from repeater.results_check.outliers_detection.outliers_detector import OutlierDetector
from tools.reflective_class_import import reflective_class_import


def get_outlier_detectors(parameters: dict) -> OutlierDetector:
    """
    :param parameters: the outliers block description from instance of Experiment class
    :return: Outlier detection object.
    """
    from repeater.results_check.outliers_detection.outliers_detector import OutlierDetector
    logger = logging.getLogger(__name__)
    if parameters["isEnabled"]:
        outlier_detectors = OutlierDetector()
        for od in parameters["Detectors"]:
            od_type = od["Type"]
            outlier_detector = reflective_class_import(class_name=od["Type"], folder_path="repeater/results_check/outliers_detection")
            outlier_detectors = outlier_detector(outlier_detectors, od["Parameters"])
            logger.debug(f"Assigned {od_type} Outlier detection criteria.")
    else:
        outlier_detectors = None
    return outlier_detectors
