"""
The TPE surrogate on a region that mixes numeric and categorical hyperparameters
(as in the hyper-heuristic search space). statsmodels' KDE only accepts numeric
data and needs strictly more observations than variables, so a categorical
hyperparameter must be encoded, and the encoding widens the feature matrix.
"""
import json
import logging
import math
import os
import unittest

import pandas as pd

os.environ["TEST_MODE"] = "UNIT_TEST"
logging.disable(logging.CRITICAL)

from configuration_selection.model.surrogate.tree_parzen_estimator import TreeParzenEstimator
from core_entities.search_space import (
    FloatHyperparameter,
    IntegerHyperparameter,
    NominalHyperparameter
)

PREFIX = "Context.SearchSpace.LLH.jMetalEvolutionStrategy"
OBJECTIVES = {"improvement": {"Name": "improvement", "Minimization": False}}


class TestTreeParzenEstimator(unittest.TestCase):

    def setUp(self):
        self.elitist = NominalHyperparameter(
            "elitist", 1, [f"{PREFIX}.elitist.true", f"{PREFIX}.elitist.false"],
            f"{PREFIX}.elitist.false")
        self.region = (
            IntegerHyperparameter("mu", 1, 1, 1000, 500),
            IntegerHyperparameter("lambda_", 1, 1, 1000, 500),
            self.elitist,
            FloatHyperparameter("mutation_probability", 1, 0, 1, 0.5),
        )
        path = os.path.join(os.path.dirname(__file__), "..", "..",
                            "Resources", "HyperHeuristic", "hh_experiment.json")
        description = json.load(open(path))
        self.surrogate_description = (
            description["ConfigurationSelection"]["Predictor"]["Model_1"]["Surrogate"])

    def _surrogate(self):
        surrogate = TreeParzenEstimator(self.surrogate_description, self.region, OBJECTIVES)
        surrogate.random_fraction = 0.0  # never skip the build at random
        return surrogate

    def _measurements(self, count):
        features = pd.DataFrame([{"mu": 100 + i * 50,
                                  "lambda_": 900 - i * 40,
                                  "elitist": self.elitist.categories[i % 2],
                                  "mutation_probability": 0.05 + i * 0.07}
                                 for i in range(count)])
        labels = pd.DataFrame({"improvement": [i * 0.7 for i in range(count)]})
        return features, labels

    def test_builds_on_a_region_with_a_categorical_hyperparameter(self):
        surrogate = self._surrogate()
        self.assertTrue(surrogate.create(*self._measurements(20)))
        # One variable type per transformed column: the BinaryEncoder widens the
        # category into two unordered columns, the three numeric ones stay continuous.
        self.assertEqual(surrogate.kde_vartypes, "ccuuc")

    def test_a_category_missing_from_a_kde_yields_a_finite_density(self):
        """statsmodels divides by zero when a categorical column has one level.

        A Configuration carrying the unseen category is one the KDE has no
        evidence for, so its density must be floored, not infinite — an infinite
        density propagates straight into the acquisition function.
        """
        surrogate = self._surrogate()
        features, labels = self._measurements(20)
        # Every top-ranked measurement shares one category, so that is the only
        # level the 'good' KDE ever sees.
        features.loc[features.index[13:], "elitist"] = self.elitist.categories[0]
        self.assertTrue(surrogate.create(features, labels))

        for category in self.elitist.categories:
            prediction = surrogate.predict(pd.Series({"mu": 500, "lambda_": 500,
                                                      "elitist": category,
                                                      "mutation_probability": 0.5}))
            for density in prediction.iloc[0]:
                self.assertTrue(math.isfinite(density), f"non-finite density for {category}")

    def test_too_few_measurements_are_declined_instead_of_raising(self):
        # The KDE needs more observations than variables: with five transformed
        # columns the build needs 2 * (5 + 1) measurements in the region.
        self.assertFalse(self._surrogate().create(*self._measurements(11)))
        self.assertTrue(self._surrogate().create(*self._measurements(12)))


if __name__ == "__main__":
    unittest.main()
