# This file contains inputs for all test cases of outliers module
import pytest

from outliers.tests.test_outliers import TestOutliers

def get_inputs_for_outliers_test(results_init, outlier_criterions_init, result_structure_init):
    # without outliers

    # Create results check values
    # Take initial values from head of this file
    # Change some values according to test
    # All artificially added outliers values mark as 'Outlier'
    # expected_results is used as check value  

    results = [{'result': {'energy': 223.3292}, 'worker': 'alpha', 'task id': 'e699ce2aaad443f88f258ae543262ea2', 'ResultValidityCheckMark': 'OK'}, 
    {'result': {'energy': 426.294}, 'worker': 'alpha', 'task id': '19e1bb7007854fc1a6a827cab28ede3f', 'ResultValidityCheckMark': 'OK'}, 
    {'result': {'energy': 392.655}, 'worker': 'alpha', 'task id': '715f2e8628374a2d8cbf794bbafb1261', 'ResultValidityCheckMark': 'OK'}, 
    {'result': {'energy': 309.047}, 'worker': 'alpha', 'task id': '9ce08308fbff411cb7cc1655ad43effe', 'ResultValidityCheckMark': 'OK'}, 
    {'result': {'energy': 240.834}, 'worker': 'alpha', 'task id': '62e90c3e1014419a950b4c4bcc6cfe80', 'ResultValidityCheckMark': 'OK'}, 
    {'result': {'energy': 426.294}, 'worker': 'alpha', 'task id': '83cfbe0ba6c143398444bcc3d54760ed', 'ResultValidityCheckMark': 'OK'}, 
    {'result': {'energy': 201.645}, 'worker': 'alpha', 'task id': 'd33175099efb4d23a6f116f5e79cb339', 'ResultValidityCheckMark': 'OK'}, 
    {'result': {'energy': 392.655}, 'worker': 'alpha', 'task id': '63e935209f2648a3bb0e43a6ea67ac34', 'ResultValidityCheckMark': 'OK'}, 
    {'result': {'energy': 426.294}, 'worker': 'alpha', 'task id': '68242f8c94ac4f849ba848785ced5ad2', 'ResultValidityCheckMark': 'OK'}, 
    {'result': {'energy': 201.645}, 'worker': 'alpha', 'task id': '315d0b8bf84f45018c14c4853baa321d', 'ResultValidityCheckMark': 'OK'}]
    outlier_criterions = outlier_criterions_init

    expected_results, actual_results, outlier_detectors_used = TestOutliers.get_expected_and_actual_values_of_outliers(results, outlier_criterions, result_structure_init)
    return expected_results, actual_results, outlier_detectors_used
