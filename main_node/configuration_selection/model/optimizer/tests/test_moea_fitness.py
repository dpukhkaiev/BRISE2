import copy

import numpy as np
import pandas as pd
import pygmo as pg
import pytest

from configuration_selection.model.optimizer.moea import MOEA
from configuration_selection.model.optimizer.optimizer_orchestrator import OptimizerOrchestrator
from configuration_selection.model.surrogate.surrogate_orchestrator import SurrogateOrchestrator
from core_entities.objectives import Objectives
from core_entities.search_space import FloatHyperparameter, NominalHyperparameter, active_mask, \
    find_parameters_activated_within_region

# test case, region, keys of the model, its surrogate and its optimizer, and how many of the objectives are taken (test
# case 3 has a surrogate and an optimizer per objective, and 'Surrogate_0' and 'Optimizer_0' serve the first one)
CASES = {
    "flat_one_objective": (13, 0, "Model", "Surrogate", "Optimizer", 1),
    "hierarchical_maximized_objective": (11, 1, "Model_1", "Surrogate", "Optimizer", 1),
    "flat_scalarized_objectives": (1, 0, "Model", "Surrogate", "Optimizer", 2),
    "flat_acquisition_function": (3, 0, "Model", "Surrogate_0", "Optimizer_0", 1),
    # 5 objectives, NSGA2, the transformers of the optimizer and of the surrogate are equal
    "hierarchical_equal_transformers": (2, 1, "Model_0", "Surrogate", "Optimizer", 5),
}
MASKED_PARAMETER = "masked_parameter"  # a region built in the test, not taken from a test case
NUMBER_OF_INDIVIDUALS = 6


class Setup:
    def __init__(self, optimizer: MOEA, surrogate, population: np.ndarray):
        self.optimizer = optimizer
        self.surrogate = surrogate
        self.population = population  # one individual per row
        self.problem = MOEA._PygmoProblem(optimizer=optimizer, surrogate=surrogate)


def _configurations(region, count, rng) -> pd.DataFrame:
    configurations = pd.DataFrame({hp.name: [hp.transform(share) for share in rng.uniform(0, 1, count)] for hp in region})
    conditional = find_parameters_activated_within_region(region)
    if conditional:
        mask = active_mask(configurations, [hp.activation_condition for hp in conditional])
        for hp in conditional:
            configurations.loc[~mask[hp.name], hp.name] = np.nan
    return configurations


def _setup(model, surrogate_key, optimizer_key, region, objectives) -> Setup:
    surrogate_description = copy.deepcopy(model[surrogate_key])
    gaussian_process = surrogate_description["Instance"].get("GaussianProcessRegressor")
    if gaussian_process:
        # With the default noise term (1e-10) the kernel matrix of the fixed kernel is nearly singular, so rows predicted
        # together and one by one differ by about 3e-5. A larger one keeps them equal up to rounding on any machine.
        gaussian_process["Parameters"]["alpha"] = 1e-6
    surrogate = SurrogateOrchestrator().get_surrogate(surrogate_description, region, objectives)
    optimizer = OptimizerOrchestrator().get_optimizer(model[optimizer_key], region, objectives)

    rng = np.random.default_rng(0)
    features = _configurations(region, 60, rng)
    labels = pd.DataFrame({name: rng.uniform(0, 1, 60) for name in objectives.names})
    assert surrogate.create(features, labels)

    optimizer._build_bounds_params_masked(surrogate)
    lower, upper = map(np.array, optimizer.bounds)
    return Setup(optimizer, surrogate, rng.uniform(lower, upper, size=(NUMBER_OF_INDIVIDUALS, len(lower))))


def _setup_with_a_masked_parameter(get_experiment) -> Setup:
    # 'only' has a single category, so all its encodings are equal and MOEA leaves it out of the search
    region = (FloatHyperparameter("f", 0, 0.0, 1.0), NominalHyperparameter("only", 0, ["only"]),
              NominalHyperparameter("c", 0, ["a", "b", "c"]))
    description, _ = get_experiment(13)
    objectives = Objectives.from_description(description["Context"]["TaskConfiguration"]["Objectives"])
    setup = _setup(description["ConfigurationSelection"]["Predictor"]["Model"], "Surrogate", "Optimizer", region,
                   objectives)
    assert list(setup.optimizer.masked_params)
    assert max(position for _, position in setup.optimizer.masked_params.values()) < len(setup.optimizer.params)
    return setup


def _setup_of_case(get_experiment, case: str) -> Setup:
    if case == MASKED_PARAMETER:
        return _setup_with_a_masked_parameter(get_experiment)
    test_case, region_index, model_key, surrogate_key, optimizer_key, number_of_objectives = CASES[case]
    description, search_space = get_experiment(test_case)
    all_objectives = Objectives.from_description(description["Context"]["TaskConfiguration"]["Objectives"])
    objectives = Objectives(tuple(all_objectives)[:number_of_objectives])
    model = description["ConfigurationSelection"]["Predictor"][model_key]
    return _setup(model, surrogate_key, optimizer_key, search_space.regions[region_index], objectives)


@pytest.fixture(params=list(CASES) + [MASKED_PARAMETER])
def setup(request, get_experiment) -> Setup:
    return _setup_of_case(get_experiment, request.param)


def _fitness_of_an_individual(setup: Setup, x: np.ndarray) -> list:
    """
    The fitness of an individual step by step: put back the parameters left out of the search, transform the individual
    back into the configuration it stands for, predict that configuration, transform the values and apply the signs.
    """
    params = list(setup.optimizer.params)
    for param, (value, position) in setup.optimizer.masked_params.items():
        params.insert(position, param)
        x = np.insert(x, position, value)
    configuration = setup.optimizer._inverse_transform_configuration(pd.DataFrame([x], columns=params))
    prediction = setup.surrogate.predict(configuration.loc[0])
    return (setup.optimizer._transform_values(prediction).values.flatten() * setup.problem.signs).tolist()


class TestFitnessOfAPopulation:

    def test_the_fitness_of_an_individual_is_the_prediction_of_its_configuration(self, setup):
        for x in setup.population:
            np.testing.assert_allclose(setup.problem.fitness(x), _fitness_of_an_individual(setup, x))

    def test_pygmo_evaluates_a_population_in_one_batch_with_the_fitness_of_each_individual(self, setup):
        problem = pg.problem(setup.problem)
        expected = np.concatenate([_fitness_of_an_individual(setup, x) for x in setup.population])

        assert problem.has_batch_fitness()
        np.testing.assert_allclose(problem.batch_fitness(setup.population.flatten()), expected)


class TestAlgorithmsEvaluateInBatches:
    """
    pygmo evaluates the population through fitness() or, for the algorithms with a batch evaluator and for the initial
    population, through batch_fitness().
    """

    @staticmethod
    def _count_evaluations(monkeypatch, setup):
        calls = {"fitness": 0, "batch_fitness": []}
        fitness, batch_fitness = MOEA._PygmoProblem.fitness, MOEA._PygmoProblem.batch_fitness
        dimension = len(setup.optimizer.params)

        def counting_fitness(problem, x):
            calls["fitness"] += 1
            return fitness(problem, x)

        def counting_batch_fitness(problem, dvs):
            calls["batch_fitness"].append(len(dvs) // dimension)
            return batch_fitness(problem, dvs)

        monkeypatch.setattr(MOEA._PygmoProblem, "fitness", counting_fitness)
        monkeypatch.setattr(MOEA._PygmoProblem, "batch_fitness", counting_batch_fitness)
        setup.optimizer.generations = 2
        setup.optimizer.optimize(setup.surrogate)
        return calls

    @pytest.mark.parametrize("case", ["flat_scalarized_objectives", "hierarchical_equal_transformers"])  # GACO, NSGA2
    def test_an_algorithm_with_a_batch_evaluator_evaluates_every_population_in_one_batch(
            self, monkeypatch, get_experiment, case):
        setup = _setup_of_case(get_experiment, case)

        calls = self._count_evaluations(monkeypatch, setup)

        assert calls["fitness"] == 0
        assert calls["batch_fitness"][0] == setup.optimizer.pop_size

    def test_an_algorithm_without_a_batch_evaluator_evaluates_its_initial_population_in_one_batch_and_then_one_by_one(
            self, monkeypatch, get_experiment):
        setup = _setup_of_case(get_experiment, "flat_one_objective")  # SADE
        setup.optimizer.pop_size = 10

        calls = self._count_evaluations(monkeypatch, setup)

        assert calls["batch_fitness"][0] == setup.optimizer.pop_size
        assert calls["fitness"] > 0


class TestReportedPredictions:
    """
    optimize() puts the parameters left out of the search back, undoes the signs and ranks the candidates itself. The
    tests of the fitness call the problem directly and never reach this.
    """

    def test_the_predictions_moea_reports_are_those_of_the_configurations_it_proposes(self, setup):
        setup.optimizer.generations = 2

        result = setup.optimizer.optimize(setup.surrogate)

        labels = ["Y"] if setup.surrogate.scalarized else setup.optimizer.objectives.names
        predicted = setup.surrogate.predict_batch(result.drop(columns=labels))
        np.testing.assert_allclose(result[labels].values, setup.optimizer._transform_values(predicted).values)
