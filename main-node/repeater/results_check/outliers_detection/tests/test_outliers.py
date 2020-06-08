import pytest
from repeater.results_check.task_errors_check import error_check
from repeater.results_check.outliers_detection.outliers_detector_selector import get_outlier_detectors

class TestOutliers:
    # in all tests size of dataset is equal 10 (as max number of repeats per each configuration)

    def test_0(self, get_sample):
        # Test #0. Initial case - no outliers in dataset 
        # All criteria are used and no outliers in dataset
        expected_results, actual_results, outlier_detectors_used = self.result_check_block(get_sample[1], get_sample[2], 0, 0, 0, 0)
        assert actual_results == expected_results
        assert outlier_detectors_used == 5

    def test_1(self, get_sample):
        # Test #1. Add single outlier
        # All criteria are used and 1 outlier is added to dataset (inputs[0] = 100223.3292)
        expected_results, actual_results, outlier_detectors_used = self.result_check_block(get_sample[1], get_sample[2], 1, 0, 0, 0)
        assert actual_results == expected_results
        assert outlier_detectors_used == 5

    def test_2(self, get_sample):
        # Test #2. Add multiple outliers
        # All criteria are used and 2 outliers are added to dataset (inputs[0] = 100223.3292, inputs[1] = 50426.294)
        expected_results, actual_results, outlier_detectors_used = self.result_check_block(get_sample[1], get_sample[2], 2, 0, 0, 0)
        assert actual_results == expected_results
        assert outlier_detectors_used == 5

    def test_3(self, get_sample):
        # Test #3. Add single outlier + single bad value
        # All criteria are used and 1 outlier + 1 bad value are added to dataset (inputs[0] = 100223.3292, inputs[1] = 'Bad value')
        expected_results, actual_results, outlier_detectors_used = self.result_check_block(get_sample[1], get_sample[2], 1, 1, 0, 0)
        assert actual_results == expected_results
        assert outlier_detectors_used == 5

    def test_4(self, get_sample):
        # Test #4. Add single outlier + multiple bad values
        # All criteria is used and 1 outlier + 2 bad values are added to dataset (inputs[0] = 100223.3292, inputs[1,2] = 'Bad value')
        expected_results, actual_results, outlier_detectors_used = self.result_check_block(get_sample[1], get_sample[2], 1, 2, 0, 0)
        assert actual_results == expected_results
        assert outlier_detectors_used == 5

    def test_5(self, get_sample):
        # Test #5. Add single outlier + reverse MinActiveNumberOfTasks and MaxActiveNumberOfTasks 
        # parameter values (MinActiveNumberOfTasks > MaxActiveNumberOfTasks) in Dixon criteria
        # All criteria are used except Dixon and 1 outlier values is added to dataset
        expected_results, actual_results, outlier_detectors_used = self.result_check_block(get_sample[1], get_sample[2], 1, 0, 1, 0)
        assert actual_results == expected_results
        assert outlier_detectors_used == 4

    def test_6(self, get_sample):
        # Test #6. Add single outlier + flexible limits for different criterias
        # 3 criteria are used (Dixon, Mad, Quartiles) and 1 outlier values is added to dataset
        # for parameter MinActiveNumberOfTasks in Chauvenet value 15 is set
        # for parameter MaxActiveNumberOfTasks in Grubbs value 5 is set
        expected_results, actual_results, outlier_detectors_used = self.result_check_block(get_sample[1], get_sample[2], 1, 0, 1, 1)
        assert actual_results == expected_results
        assert outlier_detectors_used == 4
    
    def test_7(self, get_sample):
        # Test #7. Add single outlier + all criterias are disabled
        # No criteria is used and 1 outlier values is added to dataset
        # for parameter MaxActiveNumberOfTasks in all criterias value 0 is set
        expected_results, actual_results, outlier_detectors_used = self.result_check_block(get_sample[1], get_sample[2], 1, 0, 1, 2)
        assert actual_results == expected_results
        assert outlier_detectors_used == 4

    def test_8(self, get_sample):
        # Test #8. Add single outlier + all criterias are disabled
        # No criteria is used and 1 outlier values is added to dataset
        # for parameter MaxActiveNumberOfTasks in all criterias value 0 is set
        expected_results, actual_results, outlier_detectors_used = self.result_check_block(get_sample[1], get_sample[2], 1, 0, 5, 0)
        assert actual_results == expected_results
        assert outlier_detectors_used == 0

    def result_check_block(self, tasks_sample: list, experiment_description: dict, outliers_num: int, broken_num: int, disabled_num: int, disabled_type: int):
        """
        Test function for result_check submodule of Repeater.
        Main steps:
        0. Take default tasks sample.
        1. Generate required number of outlier and broken results (if required).
        2. Change Experiment Description parameters (if required).
        3. Generate expected results.
        4. Check for errors.
        5. Check for outliers.

        :param tasks_sample: results value for 1 configuration that should be checked
        :param experiment_description: Experiment Description in json format
        :param outliers_num: specify number of generated outliers
        :param broken_num: specify number of generated broken tasks
        :param disabled_num: specify number of disabled outlier detectors
        :param disabled_type: specify type of disabled outlier detectors (1: lower bound > taskset, 2: upper bound < taskset, 0: lower bound > upper bound)

        :return: list of expected and measured results, number of used outlier detectors
        """
        # 1. Generate required number of outlier and broken results (if required).
        for i in range(0, outliers_num + broken_num):
            if i < outliers_num:
                tasks_sample[i]["result"]["energy"] = 100000
            else:
                tasks_sample[i]["result"]["energy"] = 'Bad value'

        # 2. Change Experiment Description parameters (if required).
        for i in range(0, disabled_num):
            if disabled_type == 1:
                experiment_description["OutliersDetection"]["Detectors"][i]["Parameters"]["MinActiveNumberOfTasks"] = 15
            elif disabled_type == 2:
                experiment_description["OutliersDetection"]["Detectors"][i]["Parameters"]["MaxActiveNumberOfTasks"] = 5
            else:
                experiment_description["OutliersDetection"]["Detectors"][i]["Parameters"]["MinActiveNumberOfTasks"] = 8
                experiment_description["OutliersDetection"]["Detectors"][i]["Parameters"]["MaxActiveNumberOfTasks"] = 5

        # 3. Generate expected results.
        expected_results = []
        expected_results.append('energy')
        for index in range(0,len(tasks_sample)):
            if tasks_sample[index]['result']['energy'] == 'Bad value':
                expected_results.append('Bad value')
            elif (tasks_sample[index]['result']['energy'] > 10000 and disabled_num != len(experiment_description["OutliersDetection"]["Detectors"])):
                expected_results.append('Outlier')
            else:
                expected_results.append('OK')

        # 4. Check for errors.
        result_structure = experiment_description["TaskConfiguration"]["ResultStructure"]
        expected_values_range = experiment_description["TaskConfiguration"]["ExpectedValuesRange"]
        expected_data_type = experiment_description["TaskConfiguration"]["ResultDataTypes"]
        for index, parameter in enumerate(result_structure):
            tasks_sample_error_checked = error_check(tasks_sample, parameter, expected_values_range[index], expected_data_type[index])

        # 5. Check for outliers.
        outlier_detectors = get_outlier_detectors(experiment_description["OutliersDetection"])
        results_WO_outliers, outlier_detectors_used = outlier_detectors.outlier_detection(tasks_sample_error_checked, result_structure)
        actual_results = []
        actual_results.append('energy')
        for task in results_WO_outliers:
            actual_results.append(task['ResultValidityCheckMark'])

        return expected_results, actual_results, outlier_detectors_used