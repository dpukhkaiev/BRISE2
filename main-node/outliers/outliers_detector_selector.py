import logging

from outliers.outliers_detector import OutlierDetector


def get_outlier_detectors(parameters: dict) -> OutlierDetector:
    """
    :param parameters: the outliers block description from instance of Experiment class
    :return: Outlier detection object.
    """
    from outliers.outliers_detector import OutlierDetector
    logger = logging.getLogger(__name__)
    if parameters["isEnabled"]:
        outlier_detectors = OutlierDetector()
        for od in parameters["Detectors"]:
            if od["Type"] == "Dixon":
                from outliers.dixon_test import Dixon
                outlier_detectors = Dixon(outlier_detectors, od["Parameters"])
                logger.debug("Assigned Dixon Outlier Detector.")
                continue
            if od["Type"] == "MAD":
                from outliers.mediane_absolute_deviation_method import MAD
                outlier_detectors = MAD(outlier_detectors, od["Parameters"])
                logger.debug("Assigned MAD Outlier Detector.")
                continue
            if od["Type"] == "Grubbs":
                from outliers.grubbs_test import Grubbs
                outlier_detectors = Grubbs(outlier_detectors, od["Parameters"])
                logger.debug("Assigned Grubbs Outlier Detector.")
                continue
            if od["Type"] == "Chauvenet":
                from outliers.chauvenet_criterion import Chauvenet
                outlier_detectors = Chauvenet(outlier_detectors, od["Parameters"])
                logger.debug("Assigned Chauvenet Outlier Detector.")
                continue
            if od["Type"] == "Quartiles":
                from outliers.quartiles_method import Quartiles
                outlier_detectors = Quartiles(outlier_detectors, od["Parameters"])
                logger.debug("Assigned Quartiles Outlier Detector.")
                continue
    else:
        outlier_detectors = None
    return outlier_detectors
