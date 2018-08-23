from model.regression_sweet_spot import RegressionSweetSpot
from repeater.repeater_selection import get_repeater
import pytest

from warnings import filterwarnings
filterwarnings("ignore")  # disable warnings for demonstration.


log_file_name = "file"
model_creation_config = {
    "ModelTestSize": 0.9,
    "MinimumAccuracy": 0.85,
    "ModelType": "regression",
    "FeaturesLabelsStructure": ["feature", "feature", "label"]
}
features = []
labels = []


def test_default_regressionsweetspot():
    sweet_spot = RegressionSweetSpot(log_file_name=log_file_name,
                                   test_size=model_creation_config["ModelTestSize"],
                                   features=features,
                                   labels=labels)

    assert sweet_spot.test_size == model_creation_config["ModelTestSize"]
    assert sweet_spot.all_features == features
    assert sweet_spot.all_labels == labels
    assert sweet_spot.log_file_name == log_file_name
    assert sweet_spot.model is None
    assert sweet_spot.accuracy == 0
    assert sweet_spot.solution_ready is False
    assert sweet_spot.solution_features is None
    assert sweet_spot.solution_labels is None

def test_build_model():
    features = [(1200, 1), (1200, 2), (1200, 4), (1200, 8),
                (1600, 1), (1600, 2), (1600, 4), (1600, 8),
                (2000, 1), (2000, 2), (2000, 4), (2000, 8),
                (2100, 1), (2100, 2), (2100, 4), (2100, 8),
                (2600, 1), (2600, 2), (2600, 4), (2600, 8)]
    labels = [1.2345, 1.3345, 1.4345, 1.5346,
              2.4577, 2.15454, 2.23464, 2.334634,
              2.534436, 10.5677, 10.83454, 10.93454,
              15.53453, 15.73453, 20.33453, 20.74353,
              50.44353, 100.8435, 100.9435, 110.5675]
    sweet_spot = RegressionSweetSpot(log_file_name=log_file_name,
                                     test_size=model_creation_config["ModelTestSize"],
                                     features=features,
                                     labels=labels)
    # if the model is build
    assert sweet_spot.build_model() is True  # ????
    # if score_min > current accuracy
    assert sweet_spot.build_model(score_min=0.999) is False


    #TODO - validate_model
def test_validate_model():
    search_space = {
        "threads": [1, 2, 4, 8, 16, 32],
        "frequency": [1200.0, 1300.0, 1400.0, 1600.0, 1700.0, 1800.0, 1900.0, 2000.0, 2200.0, 2300.0, 2400.0, 2500.0,
                      2700.0, 2800.0,
                      2900.0, 2901.0]
    }
    sweet_spot = RegressionSweetSpot(log_file_name=log_file_name,
                                     test_size=model_creation_config["ModelTestSize"],
                                     features=features,
                                     labels=labels)

    # sweet_spot.build_model()

    # if self.model == None
    # assert sweet_spot.validate_model(io=None, search_space=search_space) is False

    # if predicted_labels[0] >= 0


    # if predicted_labels[0] < 0



    #TODO - predict_solution
def test_predict_solution():
    search_space = {
        "threads": [1, 2, 4, 8, 16, 32],
        "frequency": [1200.0, 1300.0, 1400.0, 1600.0, 1700.0, 1800.0, 1900.0, 2000.0, 2200.0, 2300.0, 2400.0, 2500.0,
                      2700.0, 2800.0,
                      2900.0, 2901.0]
    }
    features = [(1200, 1), (1200, 2), (1200, 4), (1200, 8),
                (1600, 1), (1600, 2), (1600, 4), (1600, 8),
                (2000, 1), (2000, 2), (2000, 4), (2000, 8),
                (2100, 1), (2100, 2), (2100, 4), (2100, 8),
                (2600, 1), (2600, 2), (2600, 4), (2600, 8)]
    labels = [1.2345, 1.3345, 1.4345, 1.5346,
              2.4577, 2.15454, 2.23464, 2.334634,
              2.534436, 10.5677, 10.83454, 10.93454,
              15.53453, 15.73453, 20.33453, 20.74353,
              50.44353, 100.8435, 100.9435, 110.5675]
    sweet_spot = RegressionSweetSpot(log_file_name=log_file_name,
                                     test_size=model_creation_config["ModelTestSize"],
                                     features=features,
                                     labels=labels)
    # label, index = sweet_spot.predict_solution(io=None, search_space=search_space)

    # make first built() and validate()
    # assert label == 115
    # assert index == (1200, 32)

    #TODO - validate_solution


    #TODO - resplit_data


def test_sum_fact():
    sweet_spot = RegressionSweetSpot(log_file_name=log_file_name,
                                     test_size=model_creation_config["ModelTestSize"],
                                     features=features,
                                     labels=labels)

    for i in range(1, 1000):
        sum_exp = 0
        for j in range(i + 1):
            sum_exp = sum_exp + j
        assert sum_exp == sweet_spot.sum_fact(i)

    # fails, if num is 0 or negative in the "sum_fact()" function
    with pytest.raises(TypeError):
        sweet_spot.sum_fact(0)
    with pytest.raises(TypeError):
        sweet_spot.sum_fact(-10)


    #TODO - test_model_all_data (Error with reading task.json file: [Errno 2] No such file or directory: './Resources/task.json')
def test_test_model_all_data(tmpdir):
    data_for_task_file = {
        "DomainDescription": {
            "FeatureNames": ["frequency", "threads"],
            "DataFile": "./Resources/taskData.json",
            "AllConfigurations": "# Will be loaded from DataFile and overwritten",
            "DefaultConfiguration": [2900.0, 32]

        },
        "SelectionAlgorithm": {
            "SelectionType": "SobolSequence",
            "NumberOfInitialExperiments": 10,
            "Step": 1
        },
        "ExperimentsConfiguration": {
            "TaskName": "energy_consumption",
            "FileToRead": "Radix-500mio.csv",
            "ResultStructure": ["frequency", "threads", "energy"],
            "ResultDataTypes": ["float", "int", "float"],
            "RepeaterDecisionFunction": "student_deviation",
            "MaxRepeatsOfExperiment": 4
        },
        "ModelCreation": {
            "ModelTestSize": 0.9,
            "MinimumAccuracy": 0.85,
            "ModelType": "regression",
            "FeaturesLabelsStructure": ["feature", "feature", "label"]
        }
    }
    data_for_Radix500mio_file = "FR,TIM,EN,DC,TR,Name \
                                1200.0,48758,4907.16,2641.16,1,sort \
                                1300.0,45267.2,4657.13,2414.41,1,sort \
                                1400.0,12373.8,1280.03,860.405,4,sort \
                                1600.0,37637.9,4069.41,2400.64,1,sort \
                                1700.0,17806.7,1871.4,1192.27,2,sort \
                                1800.0,33832.6,3687.41,2117.51,1,sort \
                                1900.0,16169.8,1814.58,1125.13,2,sort \
                                2000.0,30916.3,3481.08,2128.11,1,sort \
                                2200.0,14456.6,1697.89,1055.08,2,sort \
                                2300.0,27898.5,3434.64,1949.99,1,sort \
                                2400.0,13387.5,1796.36,1139.5,2,sort \
                                2500.0,25855.4,3134.08,1946.03,1,sort \
                                2700.0,24436.4,2718.3,1635.33,1,sort \
                                2800.0,12443.6,1364.59,875.559,2,sort \
                                2900.0,23156.8,3132.78,1888.5,1,sort \
                                2901.0,11040.5,1960.54,1424.21,2,sort \
                                1300.0,2582.71,340.204,263.653,32,sort \
                                1900.0,5875.29,780.054,532.271,8,sort \
                                2500.0,1556.85,292.573,113.787,32,sort \
                                2901.0,3754.45,821.852,462.301,8,sort"

    search_space = {
        "threads": [1, 2, 4, 8, 16, 32],
        "frequency": [1200.0, 1300.0, 1400.0, 1600.0, 1700.0, 1800.0, 1900.0, 2000.0, 2200.0, 2300.0, 2400.0, 2500.0,
                      2700.0, 2800.0,
                      2900.0, 2901.0]
    }

    test_dir_resources = tmpdir.mkdir("Resources")
    test_file_resources_task = test_dir_resources.join('task.json')
    test_file_resources_task_data = test_dir_resources.join('taskData.json')
    test_dir_csv = tmpdir.mkdir("csv")
    test_csv_Radix500mio = test_dir_csv.join('Radix-500mio.csv')
    test_dir_results = tmpdir.mkdir("Results")
    test_results_radix_regression = test_dir_results.join('Radix-500mio.csvregression_model.txt')


    test_file_resources_task.write(str(data_for_task_file))
    test_csv_Radix500mio.write(data_for_Radix500mio_file)
    test_file_resources_task_data.write(str(search_space))

    # assert test_file_resources_task.read() == str(data_for_task_file)
    # assert test_csv_Radix500mio.read() == data_for_Radix500mio_file
    # assert test_file_resources_task_data.read() == str(search_space)

    features = [(1200, 1), (1200, 2), (1200, 4), (1200, 8),
                (1600, 1), (1600, 2), (1600, 4), (1600, 8),
                (2000, 1), (2000, 2), (2000, 4), (2000, 8),
                (2100, 1), (2100, 2), (2100, 4), (2100, 8),
                (2600, 1), (2600, 2), (2600, 4), (2600, 8)]
    labels = [1.2345, 1.3345, 1.4345, 1.5346,
              2.4577, 2.15454, 2.23464, 2.334634,
              2.534436, 10.5677, 10.83454, 10.93454,
              15.53453, 15.73453, 20.33453, 20.74353,
              50.44353, 100.8435, 100.9435, 110.5675]

    reg_sweet_spot = RegressionSweetSpot(log_file_name="%s%s%s_model.txt" % ("./Results/",
                                                                             data_for_task_file["ExperimentsConfiguration"]["FileToRead"],
                                                                             data_for_task_file["ModelCreation"]["ModelType"]),
                                     test_size=model_creation_config["ModelTestSize"],
                                     features=features,
                                     labels=labels)
    # reg_sweet_spot.test_model_all_data(search_space)


def test_get_result():
    WS = "WS"
    experiments = {
        "TaskName": "energy_consumption",
        "FileToRead": "Radix-500mio.csv",
        "ResultStructure": ["frequency", "threads", "energy"],
        "ResultDataTypes": ["float", "int", "float"],
        "RepeaterDecisionFunction": "student_deviation",
        "MaxRepeatsOfExperiment": 4
    }

    features = [(1200, 1), (1200, 2), (1200, 4), (1200, 8),
                (1600, 1), (1600, 2), (1600, 4), (1600, 8),
                (2000, 1), (2000, 2), (2000, 4), (2000, 8),
                (2100, 1), (2100, 2), (2100, 4), (2100, 8),
                (2600, 1), (2600, 2), (2600, 4), (2600, 8)]
    labels = [1.2345, 1.3345, 1.4345, 1.5346,
              2.4577, 2.15454, 2.23464, 2.334634,
              2.534436, 10.5677, 10.83454, 10.93454,
              15.53453, 15.73453, 20.33453, 20.74353,
              50.44353, 100.8435, 100.9435, 110.5675]
    sweet_spot = RegressionSweetSpot(log_file_name=log_file_name,
                                     test_size=model_creation_config["ModelTestSize"],
                                     features=features,
                                     labels=labels)
    repeater_type = "default"
    solution_labels, solution_features = sweet_spot.get_result(get_repeater(repeater_type, WS, experiments), features, labels, None)

    # solution_labels is None
    assert solution_labels == 1.2345
    assert solution_features == (1200, 1)

    # self.solution_labels < min(labels)
    sweet_spot.solution_labels = 1.0233
    sweet_spot.solution_features = (1200, 50)
    solution_labels, solution_features = sweet_spot.get_result(get_repeater(repeater_type, WS, experiments), features,
                                                               labels, None)
    assert solution_labels == sweet_spot.solution_labels
    assert solution_features == sweet_spot.solution_features

    # self.solution_labels > min(labels)
    sweet_spot.solution_labels = 15.0233
    sweet_spot.solution_features = (1200, 50)
    solution_labels, solution_features = sweet_spot.get_result(get_repeater(repeater_type, WS, experiments), features,
                                                               labels, None)
    assert solution_labels == 1.2345
    assert solution_features == (1200, 1)

    # solution_labels is stings
    sweet_spot.solution_labels = "qwer"
    sweet_spot.solution_features = (1200, 50)
    with pytest.raises(TypeError):
        sweet_spot.get_result(get_repeater(repeater_type, WS, experiments), features, labels, None)

    # solution_features is string
    sweet_spot.solution_labels = 1.0234
    sweet_spot.solution_features = "(1200, 50)"
    solution_labels, solution_features = sweet_spot.get_result(get_repeater(repeater_type, WS, experiments), features, labels, None)
    assert solution_labels == sweet_spot.solution_labels
    assert solution_features == sweet_spot.solution_features

    # one element of features list is string
    features = [(1200, 1), (1200, 2), (1200, 4), (1200, 8),
                (1600, 1), (1600, 2), (1600, 4), (1600, 8),
                (2000, 1), "(2000, 2)", (2000, 4), (2000, 8),
                (2100, 1), (2100, 2), (2100, 4), (2100, 8),
                (2600, 1), (2600, 2), (2600, 4), (2600, 8)]


    sweet_spot.solution_labels = None
    sweet_spot.solution_features = None

    sweet_spot = RegressionSweetSpot(log_file_name=log_file_name,
                                     test_size=model_creation_config["ModelTestSize"],
                                     features=features,
                                     labels=labels)
    solution_labels, solution_features = sweet_spot.get_result(get_repeater(repeater_type, WS, experiments), features, labels, None)

    assert solution_labels == 1.2345
    assert solution_features == (1200, 1)

    # one element of labels list is string
    labels = [1.2345, 1.3345, 1.4345, 1.5346,
              2.4577, "qwer", 2.23464, 2.334634,
              2.534436, 10.5677, 10.83454, 10.93454,
              15.53453, 15.73453, 20.33453, 20.74353,
              50.44353, 100.8435, 100.9435, 110.5675]
    with pytest.raises(TypeError):
        sweet_spot.get_result(get_repeater(repeater_type, WS, experiments), features, labels, None)