from model.model_selection import get_model
from model.regression_sweet_spot import RegressionSweetSpot
import pytest


MODEL_CREATION_CONFIG = {
        "SamplingSize": 64,
        "ModelTestSize": 0.9,
        "MinimumAccuracy": 0.85,
        "ModelType": "regression"
    }
LOG_FILE_NAME = "should_be_log_file_name"
FEATURES = []
LABELS = []


def test_get_model_without_model_test_size():
    model_creation_config = {
        "MinimumAccuracy": 0.85,
        "ModelType": "regression"
    }
    with pytest.raises(KeyError):  # fail if there is no "ModelTestSize"
        get_model(model_creation_config, LOG_FILE_NAME, FEATURES, LABELS)


def test_get_model_regression():
    result = get_model(MODEL_CREATION_CONFIG, LOG_FILE_NAME, FEATURES, LABELS)
    assert isinstance(result, RegressionSweetSpot)


def test_key_error():
    MODEL_CREATION_CONFIG["ModelType"] = "not regression"
    with pytest.raises(KeyError):
        get_model(MODEL_CREATION_CONFIG, LOG_FILE_NAME, FEATURES, LABELS)
