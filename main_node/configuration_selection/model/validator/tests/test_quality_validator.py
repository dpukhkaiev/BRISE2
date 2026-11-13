import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import r2_score

from core_entities.objectives import Objectives
from core_entities.search_space import FloatHyperparameter
from configuration_selection.model.surrogate.composite_surrogate import CompositeSurrogate
from configuration_selection.model.surrogate.sklearn_wrapper import SklearnWrapper
from configuration_selection.model.validator.quality_validator import QualityValidator

X = FloatHyperparameter("x", 0, 0.0, 10.0)
OBJECTIVES = Objectives.from_description({
    name: {"Name": name, "DataType": "float", "Minimization": True, "MinExpectedValue": 0, "MaxExpectedValue": float("inf")}
    for name in ("Y1", "Y2")})
WEIGHTS = [2, 1]  # the weighted objective stays strongly dependent on x; with [1, 2] the slopes nearly cancel
FLOAT_TRANSFORMER = {"FloatTransformer": {"SklearnFloatMinMaxScaler": {"Type": "sklearn_float_transformer"}}}


def _surrogate(objectives, value_transformers=None) -> SklearnWrapper:
    description = {
        "ConfigurationTransformers": FLOAT_TRANSFORMER,
        "Instance": {"LinearRegression": {"MultiObjective": len(objectives) > 1,
                                          "Class": "sklearn.linear_model.LinearRegression"}},
    }
    if value_transformers:
        description["ValueTransformers"] = value_transformers
    return SklearnWrapper(description, (X,), objectives)


def _validator(surrogate, threshold=0.5) -> QualityValidator:
    description = {"Split": {"HoldOut": {"TrainingSet": 0.7}}, "QualityThreshold": threshold, "Type": "quality_validator"}
    return QualityValidator(description, (X,), surrogate.objectives)


def _data(n=40):
    """Two noisy linear objectives of x, so that a linear model fits them well but not perfectly."""
    rng = np.random.default_rng(0)
    x = np.linspace(0, 10, n)
    return pd.DataFrame({"x": x}), pd.DataFrame({"Y1": 3.0 * x + 1.0 + rng.normal(0, 1.5, n),
                                                  "Y2": -2.0 * x + 5.0 + rng.normal(0, 1.5, n)})


def _trained(objectives, value_transformers=None) -> SklearnWrapper:
    surrogate = _surrogate(Objectives(tuple(OBJECTIVES.by_name(name) for name in objectives)), value_transformers)
    features, labels = _data()
    assert surrogate.create(features.iloc[::2], labels[list(objectives)].iloc[::2])
    return surrogate


def _test_rows(objectives):
    features, labels = _data()
    return features.iloc[1::2], labels[list(objectives)].iloc[1::2]


def _predicted_row_by_row(surrogate, features) -> np.ndarray:
    return np.vstack([surrogate.predict(row).values for _, row in features.iterrows()])


class TestQualityValidation:

    def test_the_score_of_a_scalarized_surrogate_compares_the_scalarized_labels(self):
        value_transformers = {"ValueScalarizator": {"WeightedSum": {"Weights": WEIGHTS, "Type": "weighted_sum"}}}
        surrogate = _trained(["Y1", "Y2"], value_transformers)
        features, labels = _test_rows(["Y1", "Y2"])
        expected = r2_score(labels.values @ np.array(WEIGHTS), _predicted_row_by_row(surrogate, features))

        is_valid, score = _validator(surrogate).validate(surrogate, features, labels)

        assert is_valid
        assert score == pytest.approx(expected)

    def test_the_score_of_a_composite_surrogate_compares_each_objective_with_its_own_surrogate(self):
        # the outer validation scores the composite of one surrogate per objective
        surrogate = CompositeSurrogate((_trained(["Y1"]), _trained(["Y2"])), (X,))
        features, labels = _test_rows(["Y1", "Y2"])
        expected = r2_score(labels.values, _predicted_row_by_row(surrogate, features))

        is_valid, score = _validator(surrogate).validate(surrogate, features, labels)

        assert is_valid
        assert score == pytest.approx(expected)

    def test_a_score_below_the_threshold_is_not_valid(self):
        surrogate = _trained(["Y1"])
        features, labels = _test_rows(["Y1"])

        assert _validator(surrogate, threshold=0.9999).validate(surrogate, features, labels) == (False, float("-inf"))

    def test_two_configurations_are_too_few_to_validate(self):
        surrogate = _trained(["Y1"])
        features, labels = _test_rows(["Y1"])

        assert _validator(surrogate).validate(surrogate, features.iloc[:2], labels.iloc[:2]) == (False, float("-inf"))
