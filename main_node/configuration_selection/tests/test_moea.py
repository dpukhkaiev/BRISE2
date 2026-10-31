"""
The MOEA optimizer searches a numeric box: pygmo builds its population from the
bounds, so every hyperparameter of a region must be encoded to a number by the
optimizer's own ConfigurationTransformers. A categorical hyperparameter without
one reaches pygmo as a raw category string.
"""
import json
import logging
import os
import unittest

os.environ["TEST_MODE"] = "UNIT_TEST"
logging.disable(logging.CRITICAL)

from configuration_selection.model.optimizer.moea import MOEA
from core_entities.search_space import (
    FloatHyperparameter,
    IntegerHyperparameter,
    NominalHyperparameter
)

ES = "Context.SearchSpace.LLH.jMetalEvolutionStrategy"
SA = "Context.SearchSpace.LLH.jMetalPySimulatedAnnealing"
OBJECTIVES = {"improvement": {"Name": "improvement", "Minimization": False}}


class TestMOEABounds(unittest.TestCase):
    """The level-1 regions of the hyper-heuristic search space."""

    def setUp(self):
        path = os.path.join(os.path.dirname(__file__), "..", "..",
                            "Resources", "HyperHeuristic", "hh_experiment.json")
        description = json.load(open(path))
        self.optimizer_description = (
            description["ConfigurationSelection"]["Predictor"]["Model_1"]["Optimizer"])

    def _assert_numeric_bounds(self, region):
        optimizer = MOEA(self.optimizer_description, region, OBJECTIVES)
        for bound in optimizer.bounds[0] + optimizer.bounds[1]:
            float(bound)  # raises exactly what pygmo raises otherwise

    def test_evolution_strategy_region(self):
        self._assert_numeric_bounds((
            IntegerHyperparameter("mu", 1, 1, 1000, 500),
            IntegerHyperparameter("lambda_", 1, 1, 1000, 500),
            NominalHyperparameter("elitist", 1, [f"{ES}.elitist.true", f"{ES}.elitist.false"],
                                  f"{ES}.elitist.false"),
            FloatHyperparameter("mutation_probability", 1, 0, 1, 0.5),
        ))

    def test_simulated_annealing_region(self):
        self._assert_numeric_bounds((
            NominalHyperparameter("mutation_type", 1,
                                  [f"{SA}.mutation_type.PermutationSwapMutation",
                                   f"{SA}.mutation_type.ScrambleMutation"],
                                  f"{SA}.mutation_type.PermutationSwapMutation"),
        ))


if __name__ == "__main__":
    unittest.main()
