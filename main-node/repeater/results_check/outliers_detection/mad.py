import numpy as np

from repeater.results_check.outliers_detection.outliers_detector_decorator import OutliersDetectionDecorator


class Mad(OutliersDetectionDecorator):
    
    def __init__(self, outlier_detector, parameters):
        super().__init__(outlier_detector, __name__, parameters)
        
    def _find_outliers(self, inputs):
        criterion_used_flag = False
        if self.lower_threshold <= len(inputs) <= self.upper_threshold:
            MAD_based_outlier = self.is_outlier(inputs)
            outliers = []
            for i in range(0, len(inputs)):
                if MAD_based_outlier[i] == True:
                    outliers.append(inputs[i])
            unique = np.unique(outliers)
            criterion_used_flag = True
            return unique, criterion_used_flag
        else:
            return [], criterion_used_flag
        
    def is_outlier(self, points, thresh=3.5):
        """
        References:
        ----------
            Boris Iglewicz and David Hoaglin (1993), "Volume 16: How to Detect and
            Handle Outliers", The ASQC Basic References in Quality Control:
            Statistical Techniques, Edward F. Mykytka, Ph.D., Editor. 
        
            Iglewicz and Hoaglin suggest using threshold ±3.5 as cut-off value 
            but this a matter of choice (±3 is also often used).
        """
        if len(points.shape) == 1:
            points = points[:,None]
        # find median value of dataset
        median = np.median(points, axis=0)
        # find deviations from median
        diff = np.sum((points - median)**2, axis=-1)
        diff = np.sqrt(diff)
        # find median of deviations
        med_abs_deviation = np.median(diff)

        # 0.6745  is the 0.75th quantile of the standard normal distribution and is used for consistency.
        modified_z_score = 0.6745 * diff / med_abs_deviation

        return modified_z_score > thresh
