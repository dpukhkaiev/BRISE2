import logging

from repeater.results_check.outliers_detection.outliers_detector import OutlierDetector


class OutliersDetectionDecorator(OutlierDetector):

    def __init__(self, outlier_detector, name, parameters):
        self.outlier_detector = outlier_detector
        self.logger = logging.getLogger(name)
        self.lower_threshold, self.upper_threshold, temp_msg = self._check_user_inputs(parameters["MinActiveNumberOfTasks"], 
                                                                                parameters["MaxActiveNumberOfTasks"])
        self.logger.info(temp_msg)

    def _validate_conditions_for_od(self, input_data, outliers, criterions_used):
        outliers_local, criterions_used_local = self._find_outliers(input_data)
        outliers.append(outliers_local)
        criterions_used.append(criterions_used_local)
        outliers, criterions_used = (self.outlier_detector._validate_conditions_for_od(input_data, outliers, criterions_used))
        return outliers, criterions_used
    
    def _check_user_inputs(self, lower_threshold_init, upper_threshold_init):
        """
        Check and fix user inputs from json
        """
        temp_msg = "Thresholds for this criteria are OK. Criteria is initialized"
        lower_threshold = float(lower_threshold_init)
        upper_threshold = float(upper_threshold_init)
        if upper_threshold < lower_threshold:
            temp_msg = ("Wrong thresholds are inserted. This criteria won`t be used")
        
        return lower_threshold, upper_threshold, temp_msg
        
    def _report_according_to_required_structure(self, config, final_results, criterions_used_number):
        super()._report_according_to_required_structure(config, final_results, criterions_used_number)
