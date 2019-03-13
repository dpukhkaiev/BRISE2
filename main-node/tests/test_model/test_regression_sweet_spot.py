from model.regression_sweet_spot import RegressionSweetSpot
from repeater.repeater_selection import get_repeater
import pytest

from warnings import filterwarnings
filterwarnings("ignore")  # disable warnings for demonstration.


G_LOG_FILE_NAME = "file"
G_MODEL_REGRESSION_CONFIG = {
    "ModelTestSize": 0.9,
    "MinimumAccuracy": 0.85,
    "ModelType": "regression"
}
G_FEATURES = [(1200, 1), (1200, 2), (1200, 4), (1200, 8),
              (1600, 1), (1600, 2), (1600, 4), (1600, 8),
              (2000, 1), (2000, 2), (2000, 4), (2000, 8),
              (2100, 1), (2100, 2), (2100, 4), (2100, 8),
              (2600, 1), (2600, 2), (2600, 4), (2600, 8)]
G_LABELS = [1.2345, 1.3345, 1.4345, 1.5346,
            2.4577, 2.15454, 2.23464, 2.334634,
            2.534436, 10.5677, 10.83454, 10.93454,
            15.53453, 15.73453, 20.33453, 20.74353,
            50.44353, 100.8435, 100.9435, 110.5675]
G_SEARCH_SPACE = [[1, 2, 4, 8, 16, 32],
                  [1200.0, 1300.0, 1400.0, 1600.0, 1700.0, 1800.0, 1900.0, 2000.0, 2200.0, 2300.0, 2400.0, 2500.0,
                   2700.0, 2800.0, 2900.0, 2901.0]]
G_WS = "WS"
G_EXPERIMENTS = {
    "TaskName": "energy_consumption",
    "FileToRead": "Radix-500mio.csv",
    "ResultStructure": ["frequency", "threads", "energy"],
    "ResultDataTypes": ["float", "int", "float"],
    "Judge": "student_deviation",
    "MaxTasksPerConfiguration": 4
}


def test_default_regression_sweet_spot():
    sweet_spot = RegressionSweetSpot(log_file_name=G_LOG_FILE_NAME,
                                     test_size=G_MODEL_REGRESSION_CONFIG["ModelTestSize"],
                                     features=G_FEATURES,
                                     labels=G_LABELS)

    assert sweet_spot.test_size == G_MODEL_REGRESSION_CONFIG["ModelTestSize"]
    assert sweet_spot.all_features == G_FEATURES
    assert sweet_spot.all_labels == G_LABELS
    assert sweet_spot.log_file_name == G_LOG_FILE_NAME
    assert sweet_spot.model is None
    assert sweet_spot.accuracy == 0
    assert sweet_spot.solution_ready is False
    assert sweet_spot.solution_features is None
    assert sweet_spot.solution_labels is None


def test_validate_model():
    sweet_spot = RegressionSweetSpot(log_file_name=G_LOG_FILE_NAME,
                                     test_size=G_MODEL_REGRESSION_CONFIG["ModelTestSize"],
                                     features=G_FEATURES,
                                     labels=G_LABELS)
    # if self.model == None
    assert sweet_spot.validate_model(io=None, search_space=G_SEARCH_SPACE) is False

# TODO - could not test because of 'load_task()' function (static paths to files) in 'test_model_all_data(...)' function

    # sweet_spot.build_model()
    # # if predicted_labels[0] >= 0
    # assert sweet_spot.validate_model(io=None, search_space=G_SEARCH_SPACE) is True
    #
    # # if predicted_labels[0] < 0
    # assert sweet_spot.validate_model(io=None, search_space=G_SEARCH_SPACE) is False


# TODO - validate_solution (could not test because of 'measure_task' inside - problem with WSClient)


def test_sum_fact():
    sweet_spot = RegressionSweetSpot(log_file_name=G_LOG_FILE_NAME,
                                     test_size=G_MODEL_REGRESSION_CONFIG["ModelTestSize"],
                                     features=G_FEATURES,
                                     labels=G_LABELS)

    for i in range(1, 1000):
        sum_exp = 0
        for j in range(i + 1):
            sum_exp = sum_exp + j
        assert sweet_spot.sum_fact(i) == sum_exp

    # fails, if num is 0 or negative
    with pytest.raises(TypeError):
        sweet_spot.sum_fact(0)
    with pytest.raises(TypeError):
        sweet_spot.sum_fact(-10)


def test_get_result():

    sweet_spot = RegressionSweetSpot(log_file_name=G_LOG_FILE_NAME,
                                     test_size=G_MODEL_REGRESSION_CONFIG["ModelTestSize"],
                                     features=G_FEATURES,
                                     labels=G_LABELS)
    repeater_type = "default"
    solution_labels, solution_features = sweet_spot.get_result(get_repeater(repeater_type, G_WS, G_EXPERIMENTS),
                                                               G_FEATURES, G_LABELS, None)

    # solution_labels is None
    assert solution_labels == 1.2345
    assert solution_features == (1200, 1)

    # self.solution_labels < min(labels)
    sweet_spot.solution_labels = 1.0233
    sweet_spot.solution_features = (1200, 50)
    solution_labels, solution_features = sweet_spot.get_result(get_repeater(repeater_type, G_WS, G_EXPERIMENTS),
                                                               G_FEATURES, G_LABELS, None)
    assert solution_labels == sweet_spot.solution_labels
    assert solution_features == sweet_spot.solution_features

    # self.solution_labels > min(labels)
    sweet_spot.solution_labels = 15.0233
    sweet_spot.solution_features = (1200, 50)
    solution_labels, solution_features = sweet_spot.get_result(get_repeater(repeater_type, G_WS, G_EXPERIMENTS),
                                                               G_FEATURES, G_LABELS, None)
    assert solution_labels == 1.2345
    assert solution_features == (1200, 1)


def test_get_result_errors():
    sweet_spot = RegressionSweetSpot(log_file_name=G_LOG_FILE_NAME,
                                     test_size=G_MODEL_REGRESSION_CONFIG["ModelTestSize"],
                                     features=G_FEATURES,
                                     labels=G_LABELS)
    repeater_type = "default"

    # solution_labels is stings
    sweet_spot.solution_labels = "string"
    sweet_spot.solution_features = (1200, 50)
    with pytest.raises(TypeError):
        sweet_spot.get_result(get_repeater(repeater_type, G_WS, G_EXPERIMENTS), G_FEATURES, G_LABELS, None)

    # solution_features is string
    sweet_spot.solution_labels = 1.0234
    sweet_spot.solution_features = "(1200, 50)"
    with pytest.raises(TypeError):
        sweet_spot.get_result(get_repeater(repeater_type, G_WS, G_EXPERIMENTS), G_FEATURES, G_LABELS, None)

    # solution_features is array
    sweet_spot.solution_features = [1200, 50]
    with pytest.raises(TypeError):
        sweet_spot.get_result(get_repeater(repeater_type, G_WS, G_EXPERIMENTS), G_FEATURES, G_LABELS, None)

    # one element of labels list is string
    labels = [1.2345, 1.3345, 1.4345, 1.5346,
              2.4577, "string", 2.23464, 2.334634,
              2.534436, 10.5677, 10.83454, 10.93454,
              15.53453, 15.73453, 20.33453, 20.74353,
              50.44353, 100.8435, 100.9435, 110.5675]
    with pytest.raises(TypeError):
        sweet_spot.get_result(get_repeater(repeater_type, G_WS, G_EXPERIMENTS), G_FEATURES, labels, None)

    # one element of features list is string
    features = [(1200, 1), (1200, 2), (1200, 4), (1200, 8),
                (1600, 1), (1600, 2), (1600, 4), (1600, 8),
                (2000, 1), "(2000, 2)", (2000, 4), (2000, 8),
                (2100, 1), (2100, 2), (2100, 4), (2100, 8),
                (2600, 1), (2600, 2), (2600, 4), (2600, 8)]
    sweet_spot.solution_labels = None
    sweet_spot.solution_features = None

    with pytest.raises(TypeError):
        RegressionSweetSpot(log_file_name=G_LOG_FILE_NAME,
                            test_size=G_MODEL_REGRESSION_CONFIG["ModelTestSize"],
                            features=features,
                            labels=G_LABELS)

    # one element of features list is array
    features = [[1200, 1], (1200, 2), (1200, 4), (1200, 8),
                (1600, 1), (1600, 2), (1600, 4), (1600, 8),
                (2000, 1), (2000, 2), (2000, 4), (2000, 8),
                (2100, 1), (2100, 2), (2100, 4), (2100, 8),
                (2600, 1), (2600, 2), (2600, 4), (2600, 8)]
    with pytest.raises(TypeError):
        RegressionSweetSpot(log_file_name=G_LOG_FILE_NAME,
                            test_size=G_MODEL_REGRESSION_CONFIG["ModelTestSize"],
                            features=features,
                            labels=G_LABELS)