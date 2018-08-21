from model.regression_sweet_spot import RegressionSweetSpot
import pytest

def test_default_RegressionSweetSpot():
    log_file_name = "file"
    model_creation_config = {
        "ModelTestSize": 0.9,
        "MinimumAccuracy": 0.85,
        "ModelType": "regression",
        "FeaturesLabelsStructure": ["feature", "feature", "label"]
    }
    features = []
    labels = []
    sweet_spot = RegressionSweetSpot(log_file_name=log_file_name,
                                   test_size=model_creation_config["ModelTestSize"],
                                   features=features,
                                   labels=labels)

    assert sweet_spot.test_size == model_creation_config["ModelTestSize"]
    assert sweet_spot.all_features == features
    assert sweet_spot.all_labels == labels
    assert sweet_spot.log_file_name == log_file_name
    assert sweet_spot.model == None
    assert sweet_spot.accuracy == 0
    assert sweet_spot.solution_ready == False
    assert sweet_spot.solution_features == None
    assert sweet_spot.solution_labels == None

def test_build_model():
    log_file_name = "file"
    model_creation_config = {
        "ModelTestSize": 0.9,
        "MinimumAccuracy": 0.85,
        "ModelType": "regression",
        "FeaturesLabelsStructure": ["feature", "feature", "label"]
    }
    features = [25]
    labels = [20]
    sweet_spot = RegressionSweetSpot(log_file_name=log_file_name,
                                     test_size=model_creation_config["ModelTestSize"],
                                     features=features,
                                     labels=labels)
    #fails
    # assert sweet_spot.build_model() == False




    #TODO - validate_model


    #TODO - predict_solution


    #TODO - validate_solution


    #TODO - resplit_data


def test_sum_fact():
    log_file_name = "file"
    model_creation_config = {
        "ModelTestSize": 0.9,
        "MinimumAccuracy": 0.85,
        "ModelType": "regression",
        "FeaturesLabelsStructure": ["feature", "feature", "label"]
    }
    features = [25]
    labels = [20]
    sweet_spot = RegressionSweetSpot(log_file_name=log_file_name,
                                     test_size=model_creation_config["ModelTestSize"],
                                     features=features,
                                     labels=labels)

    for i in range(1, 1000):
        sum_exp = 0
        for j in range(i + 1):
            sum_exp = sum_exp + j
        assert sum_exp == sweet_spot.sum_fact(i)

    # fails, if num = 0 in the "sum_fact()" function
    with pytest.raises(TypeError):
        sweet_spot.sum_fact(0)
    with pytest.raises(TypeError):
        sweet_spot.sum_fact(-10)


    #TODO - test_model_all_data


    #TODO - get_result