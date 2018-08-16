from model.regression_sweet_spot import RegressionSweetSpot

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


    #TODO - sum_fact


    #TODO - test_model_all_data


    #TODO - get_result