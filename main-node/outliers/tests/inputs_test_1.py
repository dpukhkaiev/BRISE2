# This file contains inputs for all test cases of outliers module
import pytest

from outliers.tests.test_outliers import TestOutliers

def get_inputs_for_outliers_test(results_init, outlier_criterions_init, result_structure_init):
    # As is (with 1 outlier)

    # Create results check values
    # Take initial values from head of this file
    # Change some values according to test
    # All artificially added outliers values mark as 'Outlier'
    # expected_results is used as check value  

    results = results_init
    outlier_criterions = outlier_criterions_init

    expected_results, actual_results, outlier_detectors_used = TestOutliers.get_expected_and_actual_values_of_outliers(results, outlier_criterions, result_structure_init)
    return expected_results, actual_results, outlier_detectors_used
