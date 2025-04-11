import numpy as np
from repeater.results_check.outliers_detection.outliers_detector_decorator import (
    OutliersDetectionDecorator
)
from scipy.stats import t, zscore


class Grubbs(OutliersDetectionDecorator):

    def __init__(self, outlier_detector, parameters):
        super().__init__(outlier_detector, __name__, parameters)

    def _find_outliers(self, inputs, test='two-tailed', alpha=0.05):
        criterion_used_flag = False
        if self.lower_threshold <= len(inputs) <= self.upper_threshold:
            Z = zscore(inputs, ddof=1)  # Z-score
            N = len(inputs)  # number of samples

            # calculate extreme index and the critical t value based on the test
            if test == 'two-tailed':
                extreme_ix = lambda Z: np.abs(Z).argmax()
                t_crit = lambda N: t.isf(alpha / (2. * N), N - 2)
            elif test == 'max':
                extreme_ix = lambda Z: Z.argmax()
                t_crit = lambda N: t.isf(alpha / N, N - 2)
            elif test == 'min':
                extreme_ix = lambda Z: Z.argmin()
                t_crit = lambda N: t.isf(alpha / N, N - 2)
            else:
                raise ValueError("Test must be 'min', 'max', or 'two-tailed'")

            # compute the threshold
            thresh = lambda N: (N - 1.) / np.sqrt(N) * \
                               np.sqrt(t_crit(N) ** 2 / (N - 2 + t_crit(N) ** 2))
            # create array to store outliers
            outliers = np.array([])

            # loop through the array and remove any outliers
            while abs(Z[extreme_ix(Z)]) > thresh(N):
                # update the outliers
                outliers = np.r_[outliers, inputs[extreme_ix(Z)]]
                # remove outlier from array
                inputs = np.delete(inputs, extreme_ix(Z))
                # repeat Z score
                Z = zscore(inputs, ddof=1)
                N = len(inputs)
            unique = np.unique(outliers)
            criterion_used_flag = True
            return unique, criterion_used_flag
        else:
            return [], criterion_used_flag
