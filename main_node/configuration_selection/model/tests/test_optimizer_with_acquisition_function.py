import numpy as np
import pandas as pd

from core_entities.search_space import FloatHyperparameter
from configuration_selection.model.optimizer.random_search import RandomSearch
from configuration_selection.model.surrogate.tree_parzen_estimator import TreeParzenEstimator

X = FloatHyperparameter("x", 0, 0.0, 1.0)


def _objectives(minimization):
    return {"Y1": {"Name": "Y1", "Minimization": minimization}}


class TestRandomSearchWithTreeParzenEstimator:
    """
    A Tree Parzen Estimator predicts probabilities, which only the acquisition function of the optimizer turns into
    a score per candidate.
    """

    @staticmethod
    def _trained_surrogate(objectives):
        description = {
            "ConfigurationTransformers": {
                "FloatTransformer": {"SklearnFloatMinMaxScaler": {"Type": "sklearn_float_transformer"}}},
            "Instance": {"TreeParzenEstimator": {"MultiObjective": False, "Parameters": {
                "top_n_percent": 25, "random_fraction": 0.0, "bandwidth_factor": 3, "min_bandwidth": 0.001}}},
        }
        surrogate = TreeParzenEstimator(description, (X,), objectives)
        values = np.linspace(0, 1, 60)
        assert surrogate.create(pd.DataFrame({"x": values}), pd.DataFrame({"Y1": values}))
        return surrogate

    def test_candidates_are_scored_by_the_acquisition_function_and_returned_best_first(self):
        objectives = _objectives(True)
        description = {"Instance": {"RandomSearch": {"SamplingSize": 60}},
                       "ValueTransformers": {"AcquisitionFunction": {"TPE_EI": {"Type": "tpe_ei"}}}}
        optimizer = RandomSearch(description, (X,), objectives)

        result = optimizer.optimize(self._trained_surrogate(objectives))

        assert "Y1" in result.columns  # the score is reported under the objective, where the model reads it
        assert "Y1_probability_good" not in result.columns
        assert result["Y1"].is_monotonic_increasing
        assert result.iloc[0]["x"] < 0.15  # the objective is minimized and the best observations have a small x
