import numpy as np
import pandas as pd

from core_entities.objectives import Objectives
from core_entities.search_space import FloatHyperparameter
from configuration_selection.model.surrogate.sklearn_wrapper import SklearnWrapper
from configuration_selection.model.surrogate.tree_parzen_estimator import TreeParzenEstimator

X = FloatHyperparameter("x", 0, 0.0, 10.0)
OBJECTIVES = Objectives.from_description({"Y1": {"Name": "Y1", "DataType": "float", "Minimization": True,
                                                  "MinExpectedValue": 0, "MaxExpectedValue": float("inf")}})
FLOAT_TRANSFORMER = {"FloatTransformer": {"SklearnFloatMinMaxScaler": {"Type": "sklearn_float_transformer"}}}


def _linear_regression_surrogate() -> SklearnWrapper:
    description = {
        "ConfigurationTransformers": FLOAT_TRANSFORMER,
        "Instance": {"LinearRegression": {"MultiObjective": False, "Class": "sklearn.linear_model.LinearRegression"}},
    }
    return SklearnWrapper(description, (X,), OBJECTIVES)


def _tree_parzen_estimator() -> TreeParzenEstimator:
    description = {
        "ConfigurationTransformers": FLOAT_TRANSFORMER,
        "Instance": {"TreeParzenEstimator": {"MultiObjective": False, "Parameters": {
            "top_n_percent": 25, "random_fraction": 0.0, "bandwidth_factor": 3, "min_bandwidth": 0.001}}},
    }
    return TreeParzenEstimator(description, (X,), OBJECTIVES)


def _training_data(n=40):
    values = np.linspace(0, 10, n)
    return pd.DataFrame({"x": values}), pd.DataFrame({"Y1": 3.0 * values + 1.0})


class TestSklearnWrapperPrediction:

    def test_candidates_predicted_one_at_a_time_follow_the_trained_model(self):
        surrogate = _linear_regression_surrogate()
        surrogate.create(*_training_data())

        predictions = [surrogate.predict(pd.Series({"x": x})).iloc[0, 0] for x in (0.0, 5.0, 10.0)]

        assert np.allclose(predictions, [1.0, 16.0, 31.0])

    def test_a_batch_scores_each_candidate_as_when_predicted_one_at_a_time(self):
        surrogate = _linear_regression_surrogate()
        surrogate.create(*_training_data())
        candidates = pd.DataFrame({"x": [0.5, 2.5, 7.0, 9.9]})

        batch = surrogate.predict_batch(candidates)
        one_by_one = pd.concat([surrogate.predict(row) for _, row in candidates.iterrows()], ignore_index=True)

        pd.testing.assert_frame_equal(batch, one_by_one)


class TestTreeParzenEstimatorPrediction:

    def test_a_batch_scores_each_candidate_as_when_predicted_one_at_a_time(self):
        surrogate = _tree_parzen_estimator()
        assert surrogate.create(*_training_data())
        candidates = pd.DataFrame({"x": [0.5, 2.5, 7.0, 9.9]})

        batch = surrogate.predict_batch(candidates)
        one_by_one = pd.concat([surrogate.predict(row) for _, row in candidates.iterrows()], ignore_index=True)

        pd.testing.assert_frame_equal(batch, one_by_one)

    def test_a_batch_of_one_candidate_is_scored_as_when_predicted_alone(self):
        surrogate = _tree_parzen_estimator()
        assert surrogate.create(*_training_data())
        candidate = pd.DataFrame({"x": [2.5]})

        batch = surrogate.predict_batch(candidate)

        pd.testing.assert_frame_equal(batch, surrogate.predict(candidate.iloc[0]))

    def test_batch_prediction_without_a_model_is_empty(self):
        surrogate = _tree_parzen_estimator()

        assert surrogate.predict_batch(pd.DataFrame({"x": [1.0]})).empty
