import numpy as np
from scipy.special import erfc

from repeater.results_check.outliers_detection.outliers_detector_decorator import OutliersDetectionDecorator


class Chauvenet(OutliersDetectionDecorator):
    def __init__(self, outlier_detector, parameters):
        super().__init__(outlier_detector, __name__, parameters)

    def _find_outliers(self, inputs):
        criterion_used_flag = False
        # Function calls Chauvenet algorithm and puts calculated outliers to array
        if self.lower_threshold <= len(inputs) <= self.upper_threshold:
            chauvenet_outlier = self.chauvenet(inputs)
            outliers = []
            for i in range(0,len(inputs)):
                if chauvenet_outlier[i] == False:
                    outliers.append(inputs[i])
            unique = np.unique(outliers)
            criterion_used_flag = True
            return unique, criterion_used_flag
        else:
            return [], criterion_used_flag

    def chauvenet(self, y, mean=None, stdv=None):
        if mean is None:
            mean = y.mean()          # Mean of incoming array y
        if stdv is None:
            stdv = y.std()           # Its standard deviation
        N = len(y)                   # Lenght of incoming arrays
        criterion = 1.0/(2*N)        # Chauvenet's criterion
        d = abs(y-mean)/stdv         # Distance of a value to mean in stdv's
        d /= 2.0**0.5                # The left and right tail threshold values
        prob = erfc(d)               # Area normal dist.    
        filter = prob >= criterion   # The 'accept' filter array with booleans
        return filter                # Use boolean array outside this function

    
    
