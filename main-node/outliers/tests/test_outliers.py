import sys

from outliers.outliers_detector_selector import get_outlier_detectors

results_init = [{'result': {'energy': 100223.3292}, 'worker': 'alpha', 'task id': 'e699ce2aaad443f88f258ae543262ea2', 'ResultValidityCheckMark': 'OK'}, 
    {'result': {'energy': 426.294}, 'worker': 'alpha', 'task id': '19e1bb7007854fc1a6a827cab28ede3f', 'ResultValidityCheckMark': 'OK'}, 
    {'result': {'energy': 392.655}, 'worker': 'alpha', 'task id': '715f2e8628374a2d8cbf794bbafb1261', 'ResultValidityCheckMark': 'OK'}, 
    {'result': {'energy': 309.047}, 'worker': 'alpha', 'task id': '9ce08308fbff411cb7cc1655ad43effe', 'ResultValidityCheckMark': 'OK'}, 
    {'result': {'energy': 240.834}, 'worker': 'alpha', 'task id': '62e90c3e1014419a950b4c4bcc6cfe80', 'ResultValidityCheckMark': 'OK'}, 
    {'result': {'energy': 426.294}, 'worker': 'alpha', 'task id': '83cfbe0ba6c143398444bcc3d54760ed', 'ResultValidityCheckMark': 'OK'}, 
    {'result': {'energy': 201.645}, 'worker': 'alpha', 'task id': 'd33175099efb4d23a6f116f5e79cb339', 'ResultValidityCheckMark': 'OK'}, 
    {'result': {'energy': 392.655}, 'worker': 'alpha', 'task id': '63e935209f2648a3bb0e43a6ea67ac34', 'ResultValidityCheckMark': 'OK'}, 
    {'result': {'energy': 426.294}, 'worker': 'alpha', 'task id': '68242f8c94ac4f849ba848785ced5ad2', 'ResultValidityCheckMark': 'OK'}, 
    {'result': {'energy': 201.645}, 'worker': 'alpha', 'task id': '315d0b8bf84f45018c14c4853baa321d', 'ResultValidityCheckMark': 'OK'}]

outliers_criterion_init = [{'Parameters': {'MaxActiveNumberOfTasks': 30, 'MinActiveNumberOfTasks': 3}, 'Type': 'Dixon'}, 
    {'Parameters': {'MaxActiveNumberOfTasks': 'Inf', 'MinActiveNumberOfTasks': 0}, 'Type': 'Chauvenet'}, 
    {'Parameters': {'MaxActiveNumberOfTasks': 'Inf', 'MinActiveNumberOfTasks': 0}, 'Type': 'MAD'}, 
    {'Parameters': {'MaxActiveNumberOfTasks': 'Inf', 'MinActiveNumberOfTasks': 0}, 'Type': 'Grubbs'}, 
    {'Parameters': {'MaxActiveNumberOfTasks': 'Inf', 'MinActiveNumberOfTasks': 0}, 'Type': 'Quartiles'}]

result_structure_init = ['energy']
class TestOutliers:
    # in all tests size of dataset is equal 10 (as max number of repeats per each configuration)

    def test_0_answer(self):
        # Test #0. Initial case - no outliers in dataset 
        # All criteria are used and no outliers in dataset
        from outliers.tests.inputs_test_0 import get_inputs_for_outliers_test
        expected_results, actual_results, outlier_detectors_used = get_inputs_for_outliers_test(results_init, outliers_criterion_init, result_structure_init)
        # [['energy', 223.3292, 426.294, 392.655, 309.047, 240.834, 426.294, 201.645, 392.655, 426.294, 201.645]]
        assert actual_results == [expected_results]
        assert outlier_detectors_used == 5

    def test_1_answer(self):
        # Test #1. Add single outlier
        # All criteria are used and 1 outlier is added to dataset (inputs[0] = 100223.3292)
        from outliers.tests.inputs_test_1 import get_inputs_for_outliers_test
        expected_results, actual_results, outlier_detectors_used = get_inputs_for_outliers_test(results_init, outliers_criterion_init, result_structure_init)
        # Expected output from outlier detection module: 
        # [['energy', 'Outlier', 426.294, 392.655, 309.047, 240.834, 426.294, 201.645, 392.655, 426.294, 201.645]]
        assert actual_results == [expected_results]
        assert outlier_detectors_used == 5

    def test_2_answer(self):
        # Test #2. Add multiple outliers
        # All criteria are used and 2 outliers are added to dataset (inputs[0] = 100223.3292, inputs[1] = 50426.294)
        from outliers.tests.inputs_test_2 import get_inputs_for_outliers_test
        expected_results, actual_results, outlier_detectors_used = get_inputs_for_outliers_test(results_init, outliers_criterion_init, result_structure_init)
        # Expected output from outlier detection module: 
        # [['energy', 'Outlier', "Outlier", 392.655, 309.047, 240.834, 426.294, 201.645, 392.655, 426.294, 201.645]]
        assert actual_results == [expected_results]
        assert outlier_detectors_used == 5

    def test_3_answer(self):
        # Test #3. Add single outlier + single bad value
        # All criteria are used and 1 outlier + 1 bad value are added to dataset (inputs[0] = 100223.3292, inputs[1] = 'Bad value')
        from outliers.tests.inputs_test_3 import get_inputs_for_outliers_test
        expected_results, actual_results, outlier_detectors_used = get_inputs_for_outliers_test(results_init, outliers_criterion_init, result_structure_init)
        # Expected output from outlier detection module: 
        # [['energy', 'Outlier', 'Bad value', 392.655, 309.047, 240.834, 426.294, 201.645, 392.655, 426.294, 201.645]]
        assert actual_results == [expected_results]
        assert outlier_detectors_used == 5

    def test_4_answer(self):
        # Test #4. Add single outlier + multiple bad values
        # All criteria is used and 1 outlier + 2 bad values are added to dataset (inputs[0] = 100223.3292, inputs[1,2] = 'Bad value')
        from outliers.tests.inputs_test_4 import get_inputs_for_outliers_test
        expected_results, actual_results, outlier_detectors_used = get_inputs_for_outliers_test(results_init, outliers_criterion_init, result_structure_init)
        # Expected output from outlier detection module: 
        # [['energy', 'Outlier', 'Bad value', 'Bad value', 309.047, 240.834, 426.294, 201.645, 392.655, 426.294, 201.645]]
        assert actual_results == [expected_results]
        assert outlier_detectors_used == 5

    def test_5_answer(self):
        # Test #5. Add single outlier + reverse MinActiveNumberOfTasks and MaxActiveNumberOfTasks 
        # parameter values (MinActiveNumberOfTasks > MaxActiveNumberOfTasks) in Dixon criteria
        # All criteria are used except Dixon and 1 outlier values is added to dataset
        # Expected output from outlier detection module: 
        # [['energy', 'Outlier', 426.294, 392.655, 309.047, 240.834, 426.294, 201.645, 392.655, 426.294, 201.645]]
        from outliers.tests.inputs_test_5 import get_inputs_for_outliers_test
        expected_results, actual_results, outlier_detectors_used = get_inputs_for_outliers_test(results_init, outliers_criterion_init, result_structure_init)
        assert actual_results == [expected_results]
        assert outlier_detectors_used == 4

    def test_6_answer(self):
        # Test #6. Add single outlier + flexible limits for different criterias
        # 3 criteria are used (Dixon, Mad, Quartiles) and 1 outlier values is added to dataset
        # for parameter MinActiveNumberOfTasks in Chauvenet value 15 is set
        # for parameter MaxActiveNumberOfTasks in Grubbs value 5 is set
        from outliers.tests.inputs_test_6 import get_inputs_for_outliers_test
        expected_results, actual_results, outlier_detectors_used = get_inputs_for_outliers_test(results_init, outliers_criterion_init, result_structure_init)
        # Expected output from outlier detection module: 
        # [['energy', 'Outlier', 426.294, 392.655, 309.047, 240.834, 426.294, 201.645, 392.655, 426.294, 201.645]]        
        assert actual_results == [expected_results]
        assert outlier_detectors_used == 3
    
    def test_7_answer(self):
        # Test #7. Add single outlier + all criterias are disabled
        # No criteria is used and 1 outlier values is added to dataset
        # for parameter MaxActiveNumberOfTasks in all criterias value 0 is set
        from outliers.tests.inputs_test_7 import get_inputs_for_outliers_test
        expected_results, actual_results, outlier_detectors_used = get_inputs_for_outliers_test(results_init, outliers_criterion_init, result_structure_init)
        # Expected output from outlier detection module: 
        # [['energy', 100223.3292, 426.294, 392.655, 309.047, 240.834, 426.294, 201.645, 392.655, 426.294, 201.645]]        
        assert actual_results == [expected_results]
        assert outlier_detectors_used == 0
    
    @staticmethod
    def get_expected_and_actual_values_of_outliers(results, outlier_criterions, result_structure_init):
        expected_results = []
        expected_results.append('energy')
        for index in range(0,len(results)):
            if results[index]['result']['energy'] == 'Bad value':
                expected_results.append('Bad value')
            elif results[index]['result']['energy'] > 10000:
                expected_results.append('Outlier')
            else:
                expected_results.append('OK')   
        result_structure = result_structure_init
        outlier_detectors = get_outlier_detectors(outlier_criterions)
        # call outlier_detection module and get his output
        results_WO_outliers, outlier_detectors_used = outlier_detectors.outlier_detection(results, result_structure)
        actual_results = []
        actual_results.append('energy')
        for task in results_WO_outliers:
            actual_results.append(task['ResultValidityCheckMark'])

        return expected_results, [actual_results], outlier_detectors_used
