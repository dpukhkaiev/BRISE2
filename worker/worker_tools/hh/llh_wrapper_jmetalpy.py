import inspect
from copy import copy
from functools import lru_cache
from typing import List, Mapping, Type

import jmetal
import jmetal.util.termination_criterion as termination
from jmetal.core.problem import Problem
from jmetal.core.algorithm import Algorithm
from jmetal.core.solution import PermutationSolution, FloatSolution, BinarySolution

from worker_tools.hh.llh_runner import ILLHWrapper


class HashableDict(dict):
    def __hash__(self) -> int:
        return hash(tuple(sorted(self.items())))

    def __eq__(self, other) -> bool:
        return hash(self) == hash(other)


class JMetalPyWrapper(ILLHWrapper):

    def __init__(self, problem_type=None):
        super().__init__()
        # add choice
        self.problem_type = problem_type
        self._is_parameter_control_enabled = False
        if self.problem_type == "permutation_problem" or self.problem_type is None:
            self._initial_solutions: List[PermutationSolution] = []
        elif self.problem_type == "float_problem":
            self._initial_solutions: List[FloatSolution] = []
        elif self.problem_type == "binary_problem":
            self._initial_solutions: List[BinarySolution] = []
        else:
            raise NotImplementedError("Your type of problem can not be solved by heuristics yet!")
        self._solution_generator = None

    def construct(self, hyperparameters: Mapping, scenario: Mapping, parameter_control_info: Mapping) -> None:

        self._is_parameter_control_enabled = scenario["isParameterControlEnabled"]

        # The chosen LLH's value is the absolute-path prefix its own children (mu, lambda_, mutation_type, ...)
        # are named under.
        llh_path = hyperparameters["Context.SearchSpace.LLH"]
        llh_name = llh_path.split(".")[-1]

        # Constructing meta-heuristics initialization arguments (components + simple hyperparameters).
        # jMetalPy's constructor kwargs are fixed names, so build init_args explicitly from BRISE's
        # absolute parameter paths rather than passing the hyperparameters dict through.
        init_args = {}

        for kwarg in ("mu", "lambda_", "population_size", "offspring_population_size"):
            path = f"{llh_path}.{kwarg}"
            if path in hyperparameters:
                init_args[kwarg] = hyperparameters[path]

        # jMetalPy.EvolutionStrategy requires lambda_ >= mu (offspring pool must be able to
        # fill the next population); swap if the sampled values violate that.
        if llh_name == "jMetalPyEvolutionStrategy" and "lambda_" in init_args and "mu" in init_args:
            if init_args["lambda_"] < init_args["mu"]:
                self.logger.warning(
                    f"Values for 'lambda_'({init_args['lambda_']}) and 'mu'({init_args['mu']}) "
                    f"were swapped: jMetalPy.EvolutionStrategy requires lambda_ >= mu."
                )
                init_args["lambda_"], init_args["mu"] = init_args["mu"], init_args["lambda_"]

        # offspring_population_size should be even
        if "offspring_population_size" in init_args:
            init_args["offspring_population_size"] += init_args["offspring_population_size"] % 2

        # elitist should be bool
        elitist_path = f"{llh_path}.elitist"
        if elitist_path in hyperparameters:
            init_args["elitist"] = hyperparameters[elitist_path].split(".")[-1] == "True"

        crossover_type_path = f"{llh_path}.crossover_type"
        if crossover_type_path in hyperparameters:
            import jmetal.operator.crossover as crossover
            crossover_value = hyperparameters[crossover_type_path]
            crossover_class = JMetalPyWrapper._get_class_from_module(name=crossover_value.split(".")[-1],
                                                                     module=crossover)
            init_args["crossover"] = crossover_class(hyperparameters[f"{crossover_value}.crossover_probability"])

        mutation_type_path = f"{llh_path}.mutation_type"
        if mutation_type_path in hyperparameters:
            import jmetal.operator.mutation as mutation
            mutation_value = hyperparameters[mutation_type_path]
            mutation_class = JMetalPyWrapper._get_class_from_module(name=mutation_value.split(".")[-1],
                                                                    module=mutation)
            init_args["mutation"] = mutation_class(hyperparameters[f"{mutation_value}.mutation_probability"])

        selection_type_path = f"{llh_path}.selection_type"
        if selection_type_path in hyperparameters:
            selection_type = hyperparameters[selection_type_path].split(".")[-1]
            if selection_type == 'ReuletteWheelSelection':
                from jmetal.util.comparator import MultiComparator
                from jmetal.util.density_estimator import CrowdingDistance
                from jmetal.util.ranking import FastNonDominatedRanking
                init_args["selection"] = MultiComparator(
                    [FastNonDominatedRanking.get_comparator(), CrowdingDistance.get_comparator()])
            else:
                import jmetal.operator.selection as selection
                selection_class = JMetalPyWrapper._get_class_from_module(name=selection_type,
                                                                         module=selection)
                init_args["selection"] = selection_class()

        termination_class = JMetalPyWrapper._get_class_from_module(name=scenario["Budget"]["Type"],
                                                                   module=termination)
        init_args["termination_criterion"] = termination_class(scenario["Budget"]["Amount"])

        # making dict hashable enables using LRU cache
        problem_init_params = HashableDict(scenario['InitializationParameters'])
        problem = JMetalPyWrapper._get_problem(problem_name=scenario['Problem'],
                                               init_params=problem_init_params)
        init_args["problem"] = problem
        # Attach initial solutions.
        self.load_initial_solutions(parameter_control_info, problem)

        if llh_name == "jMetalPySimulatedAnnealing":
            init_args["solution_generator"] = self._solution_generator
        else:
            init_args['population_generator'] = self._solution_generator

        # Instantiate Metaheuristic object
        self._llh_algorithm = JMetalPyWrapper._get_algorithm_class(llh_name)(**init_args)

    def run_and_report(self) -> Mapping:
        self._llh_algorithm.run()

        # Construct the results
        current_objective = self._llh_algorithm.get_result().objectives[0]
        if len(self._initial_solutions) <= 0:
            improvement = 0
        else:
            best_previously_existing_solution = max(self._initial_solutions, key=lambda sol: sol.objectives[0])
            best_previous_objective = best_previously_existing_solution.objectives[0]
            improvement = (best_previous_objective - current_objective) / best_previous_objective

        result = {
            "objective": current_objective,
            "improvement": improvement,
            "parameter_control_info": {
                "solutions": [s.variables for s in self._llh_algorithm.solutions]
            }
        }
        return result

    # Helper methods
    def load_initial_solutions(self, parameter_control_info: Mapping, problem: Problem) -> None:
        self.parameter_control_info = parameter_control_info
        if (parameter_control_info and 'solutions' in self.parameter_control_info.keys() and len(
                self.parameter_control_info['solutions']) > 0):
            from jmetal.util.generator import InjectorGenerator
            one_sol_variables = self.parameter_control_info['solutions'][0]
            if self.problem_type == "permutation_problem" or self.problem_type is None:
                solution = PermutationSolution(number_of_variables=problem.number_of_variables,
                                               number_of_objectives=problem.number_of_objectives)
            elif self.problem_type == "float_problem":
                solution = FloatSolution(lower_bound=problem.lower_bound,
                                         upper_bound=problem.upper_bound,
                                         number_of_objectives=problem.number_of_objectives)
            elif self.problem_type == "binary_problem":
                solution = BinarySolution(number_of_variables=problem.number_of_variables,
                                          number_of_objectives=problem.number_of_objectives)
            solution.variables = one_sol_variables
            self._initial_solutions.append(problem.evaluate(solution))

            for one_sol_variables in self.parameter_control_info['solutions'][1:]:
                solution = copy(solution)
                solution.variables = one_sol_variables
                self._initial_solutions.append(problem.evaluate(solution))
            if self._is_parameter_control_enabled:
                generator = InjectorGenerator(solutions=self._initial_solutions)
            else:
                from jmetal.util.generator import RandomGenerator
                generator = RandomGenerator()
        else:
            from jmetal.util.generator import RandomGenerator
            generator = RandomGenerator()
        self._solution_generator = generator

    @staticmethod
    @lru_cache(maxsize=10, typed=True)
    def _get_problem(problem_name: str, init_params: dict) -> jmetal.core.problem.Problem:
        import jmetal.problem as problems
        problem = JMetalPyWrapper._get_class_from_module(name=problem_name, module=problems)
        return problem(**init_params)

    @staticmethod
    @lru_cache(maxsize=10, typed=True)
    def _get_algorithm_class(mh_name: str) -> Algorithm.__class__:
        relative_mh_name = mh_name.split(".")[-1]
        if relative_mh_name == 'jMetalPyGeneticAlgorithm':
            from jmetal.algorithm.singleobjective.genetic_algorithm import \
                GeneticAlgorithm as Alg
        elif relative_mh_name == 'jMetalPySimulatedAnnealing':
            from jmetal.algorithm.singleobjective.simulated_annealing import \
                SimulatedAnnealing as Alg
        elif relative_mh_name == 'jMetalPyEvolutionStrategy':
            from jmetal.algorithm.singleobjective.evolution_strategy import \
                EvolutionStrategy as Alg
        elif relative_mh_name == 'jMetalPyLocalSearch':
            from jmetal.algorithm.singleobjective.local_search import \
                LocalSearch as Alg
        else:
            raise KeyError(f"Unknown algorithm {relative_mh_name}.")
        return Alg

    @staticmethod
    @lru_cache(maxsize=10, typed=True)
    def _get_class_from_module(name: str, module: object) -> Type:
        classes = inspect.getmembers(module, lambda member: inspect.isclass(member))
        try:
            index = [name_and_class[0] for name_and_class in classes].index(name.split(".")[-1])
        except IndexError:
            raise IndexError(f"Unable to locate desired Operator {name} in provided Module {module.__name__}")
        return classes[index][1]


class JMetalPyWrapperTuned(JMetalPyWrapper):
    def construct(self, hyperparameters: Mapping, scenario: Mapping, parameter_control_info: Mapping) -> None:
        problem_init_params = HashableDict(scenario['InitializationParameters'])
        problem = self._get_problem(scenario['Problem'], problem_init_params)
        self.load_initial_solutions(parameter_control_info, problem)

        from jmetal.operator.mutation import PermutationSwapMutation

        termination_criterion_cls = self._get_class_from_module(name=scenario["Budget"]["Type"], module=termination)
        termination_criterion = termination_criterion_cls(scenario["Budget"]["Amount"])

        mh_name = hyperparameters["Context.SearchSpace.LLH"].split(".")[-1]
        if mh_name == "GeneticAlgorithm":
            from jmetal.algorithm.singleobjective.genetic_algorithm import (
                GeneticAlgorithm
            )
            from jmetal.operator.crossover import CXCrossover
            from jmetal.operator.selection import BinaryTournamentSelection
            self._llh_algorithm = GeneticAlgorithm(
                problem=problem,
                population_size=385,
                offspring_population_size=878,
                mutation=PermutationSwapMutation(0.966),
                crossover=CXCrossover(0.93),
                selection=BinaryTournamentSelection(),
                termination_criterion=termination_criterion,
                population_generator=self._solution_generator
            )

        elif mh_name == "SimulatedAnnealing":
            from jmetal.algorithm.singleobjective.simulated_annealing import (
                SimulatedAnnealing
            )
            self._llh_algorithm = SimulatedAnnealing(
                problem=problem,
                mutation=PermutationSwapMutation(0.8954537798654278),
                termination_criterion=termination_criterion,
                solution_generator=self._solution_generator
            )

        elif mh_name == "EvolutionStrategy":
            from jmetal.algorithm.singleobjective.evolution_strategy import (
                EvolutionStrategy
            )
            self._llh_algorithm = EvolutionStrategy(
                problem=problem,
                mu=5,
                lambda_=22,
                elitist=True,
                mutation=PermutationSwapMutation(0.999238856031505),
                termination_criterion=termination_criterion,
                population_generator=self._solution_generator
            )
        else:
            self.logger.error(f"Wrong meta-heuristic name: {mh_name}")


class JMetalPyWrapperDefault(JMetalPyWrapper):
    def construct(self, hyperparameters: Mapping, scenario: Mapping, parameter_control_info: Mapping) -> None:
        problem_init_params = HashableDict(scenario['InitializationParameters'])
        problem = self._get_problem(scenario['Problem'], problem_init_params)
        self.load_initial_solutions(parameter_control_info, problem)

        from jmetal.operator.mutation import PermutationSwapMutation

        termination_criterion_cls = self._get_class_from_module(name=scenario["Budget"]["Type"], module=termination)
        termination_criterion = termination_criterion_cls(scenario["Budget"]["Amount"])

        mh_name = hyperparameters["Context.SearchSpace.LLH"].split(".")[-1]
        if mh_name == "GeneticAlgorithm":
            from jmetal.algorithm.singleobjective.genetic_algorithm import (
                GeneticAlgorithm
            )
            from jmetal.operator.crossover import CXCrossover
            from jmetal.operator.selection import BinaryTournamentSelection
            self._llh_algorithm = GeneticAlgorithm(
                problem=problem,
                population_size=100,
                offspring_population_size=100,
                mutation=PermutationSwapMutation(0.5),
                crossover=CXCrossover(0.5),
                selection=BinaryTournamentSelection(),
                termination_criterion=termination_criterion,
                population_generator=self._solution_generator
            )

        elif mh_name == "SimulatedAnnealing":
            from jmetal.algorithm.singleobjective.simulated_annealing import (
                SimulatedAnnealing
            )
            self._llh_algorithm = SimulatedAnnealing(
                problem=problem,
                mutation=PermutationSwapMutation(0.5),
                termination_criterion=termination_criterion,
                solution_generator=self._solution_generator
            )

        elif mh_name == "EvolutionStrategy":
            from jmetal.algorithm.singleobjective.evolution_strategy import (
                EvolutionStrategy
            )
            self._llh_algorithm = EvolutionStrategy(
                problem=problem,
                mu=500,
                lambda_=500,
                elitist=False,
                mutation=PermutationSwapMutation(0.5),
                termination_criterion=termination_criterion,
                population_generator=self._solution_generator
            )
        else:
            self.logger.error(f"Wrong meta-heuristic name: {mh_name}")
