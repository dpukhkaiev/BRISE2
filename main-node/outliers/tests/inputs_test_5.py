# This file contains inputs for all test cases of outliers module
import pytest

from outliers.tests.test_outliers import TestOutliers

def get_inputs_for_outliers_test(results_init, outlier_criterions_init, result_structure_init):
    # If outliers criterions MinActiveNumberOfTasks > MaxActiveNumberOfTasks
    # with 1 outlier

    # Create results check values
    # Take initial values from head of this file
    # Change some values according to test
    # All artificially added outliers values mark as 'Outlier'
    # expected_results is used as check value  

    results = results_init
    outlier_criterions = [{'Parameters': {'MaxActiveNumberOfTasks': 3, 'MinActiveNumberOfTasks': 30}, 'Type': 'Dixon'}, 
    {'Parameters': {'MaxActiveNumberOfTasks': 'Inf', 'MinActiveNumberOfTasks': 0}, 'Type': 'Chauvenet'}, 
    {'Parameters': {'MaxActiveNumberOfTasks': 'Inf', 'MinActiveNumberOfTasks': 0}, 'Type': 'MAD'}, 
    {'Parameters': {'MaxActiveNumberOfTasks': 'Inf', 'MinActiveNumberOfTasks': 0}, 'Type': 'Grubbs'}, 
    {'Parameters': {'MaxActiveNumberOfTasks': 'Inf', 'MinActiveNumberOfTasks': 0}, 'Type': 'Quartiles'}]

    expected_results, actual_results, outlier_detectors_used = TestOutliers.get_expected_and_actual_values_of_outliers(results, outlier_criterions, result_structure_init)
    return expected_results, actual_results, outlier_detectors_used
