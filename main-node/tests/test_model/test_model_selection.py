from model.model_selection import get_model
from model.regression_sweet_spot import RegressionSweetSpot
import pytest


# fail if there is no "ModelTestSize"
def test_get_model_without_ModelTestSize():
    model_creation_config = {
        # "ModelTestSize": 0.9,
        "MinimumAccuracy": 0.85,
        "ModelType": "regression",
        "FeaturesLabelsStructure": ["feature", "feature", "label"]
    }
    log_file_name = "123"
    features = []
    labels = []

    with pytest.raises(KeyError):
        get_model(model_creation_config, log_file_name, features, labels)

def test_get_model_regression():
    model_creation_config = {
        "ModelTestSize": 0.9,
        "MinimumAccuracy": 0.85,
        "ModelType": "regression",
        "FeaturesLabelsStructure": ["feature", "feature", "label"]
    }
    log_file_name = "123"
    features = []
    labels = []
    result = get_model(model_creation_config, log_file_name, features, labels)
    assert isinstance(result, RegressionSweetSpot)

def test_KeyError():
    log_file_name = "123"
    features = []
    labels = []
    model_creation_config2 = {
        "ModelTestSize": 0.9,
        "MinimumAccuracy": 0.85,
        "ModelType": "not regression",
        "FeaturesLabelsStructure": ["feature", "feature", "label"]
    }

    with pytest.raises(KeyError):
        get_model(model_creation_config2, log_file_name, features, labels)