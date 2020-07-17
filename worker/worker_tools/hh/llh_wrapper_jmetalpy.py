import inspect
from copy import copy
from typing import Mapping, Type, List
from functools import lru_cache

import jmetal
from jmetal.core.algorithm import Algorithm
from jmetal.core.problem import Problem
from jmetal.core.solution import PermutationSolution
import jmetal.util.termination_criterion as termination

from worker_tools.hh.llh_runner import ILLHWrapper


class HashableDict(dict):
    def __hash__(self) -> int:
        return hash(tuple(sorted(self.items())))

    def __eq__(self, other) -> bool:
        return hash(self) == hash(other)


class JMetalPyWrapper(ILLHWrapper):

    def __init__(self):
        super().__init__()
        self._initial_solutions: List[PermutationSolution] = []
        self._solution_generator = None

    def construct(self, hyperparameters: Mapping, scenario: Mapping, warm_startup_info: Mapping) -> None:

        # Constructing meta-heuristics initialization arguments (components + simple hyperparameters)
        init_args = dict(copy(hyperparameters))

        if "crossover_type" in init_args:
            import jmetal.operator.crossover as crossover
            crossover_class = JMetalPyWrapper._get_class_from_module(name=init_args.pop("crossover_type"),
                                                                     module=crossover)
            init_args["crossover"] = crossover_class(init_args.pop("crossover_probability"))

        if "mutation_type" in init_args:
            import jmetal.operator.mutation as mutation
            mutation_class = JMetalPyWrapper._get_class_from_module(name=init_args.pop("mutation_type"),
                                                                    module=mutation)
            init_args["mutation"] = mutation_class(init_args.pop("mutation_probability"))

        if "selection_type" in init_args:
            selection_type = init_args.pop('selection_type')
            if selection_type == 'ReuletteWheelSelection':
                # TODO: add decoupling of comparators.
                from jmetal.util.comparator import MultiComparator
                from jmetal.util.ranking import FastNonDominatedRanking
                from jmetal.util.density_estimator import CrowdingDistance
                init_args["selection"] = MultiComparator(
                    [FastNonDominatedRanking.get_comparator(), CrowdingDistance.get_comparator()])
            else:
                import jmetal.operator.selection as selection
                selection_class = JMetalPyWrapper._get_class_from_module(name=selection_type,
                                                                         module=selection)
                init_args["selection"] = selection_class()

        # Add all non-component Metaheuristic parameters
        if "offspring_population_size" in init_args:
            offsp_population = init_args.pop("offspring_population_size")
            # offspring_population_size should be even
            offsp_population += offsp_population % 2
            init_args['offspring_population_size'] = offsp_population

        # elitist should be bool
        if "elitist" in init_args:
            init_args['elitist'] = True if init_args.pop('elitist') == "True" else False

        if "population_size" in init_args:
            init_args["population_size"] = init_args.pop("population_size")

        termination_class = JMetalPyWrapper._get_class_from_module(name=scenario["Budget"]["Type"],
                                                                   module=termination)
        init_args["termination_criterion"] = termination_class(scenario["Budget"]["Amount"])

        # making dict hashable enables using LRU cache
        problem_init_params = HashableDict(scenario['problem_initialization_parameters'])
        problem = JMetalPyWrapper._get_problem(problem_name=scenario['Problem'],
                                                            init_params=problem_init_params)
        init_args["problem"] = problem
        # Attach initial solutions.
        self.load_initial_solutions(warm_startup_info, problem)

        llh_name = init_args.pop("low level heuristic")
        if llh_name == "jMetalPy.SimulatedAnnealing":
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
            "warm_startup_info": {
                "paths": [s.variables for s in self._llh_algorithm.solutions]
            }
        }
        return result

    # Helper methods
    def load_initial_solutions(self, warm_startup_info: Mapping, problem: Problem) -> None:
        self.warm_startup_info = warm_startup_info
        if warm_startup_info and 'paths' in self.warm_startup_info.keys() and len(self.warm_startup_info['paths']) > 0:
            from jmetal.util.generator import InjectorGenerator
            one_sol_variables = self.warm_startup_info['paths'][0]
            solution = PermutationSolution(number_of_variables=problem.number_of_variables,
                                           number_of_objectives=problem.number_of_objectives)
            solution.variables = one_sol_variables
            self._initial_solutions.append(problem.evaluate(solution))

            for one_sol_variables in self.warm_startup_info['paths'][1:]:
                solution = copy(solution)
                solution.variables = one_sol_variables
                self._initial_solutions.append(problem.evaluate(solution))
            generator = InjectorGenerator(solutions=self._initial_solutions)

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
    def _get_algorithm_class(mh_name: str) -> jmetal.core.algorithm.Algorithm.__class__:
        if mh_name == 'jMetalPy.GeneticAlgorithm':
            from jmetal.algorithm.singleobjective.genetic_algorithm import GeneticAlgorithm as Alg
        elif mh_name == 'jMetalPy.SimulatedAnnealing':
            from jmetal.algorithm.singleobjective.simulated_annealing import SimulatedAnnealing as Alg
        elif mh_name == 'jMetalPy.EvolutionStrategy':
            from jmetal.algorithm.singleobjective.evolution_strategy import EvolutionStrategy as Alg
        elif mh_name == 'jMetalPy.LocalSearch':
            from jmetal.algorithm.singleobjective.local_search import LocalSearch as Alg
        else:
            raise KeyError(f"Unknown algorithm {mh_name}.")
        return Alg

    @staticmethod
    @lru_cache(maxsize=10, typed=True)
    def _get_class_from_module(name: str, module: object) -> Type:
        classes = inspect.getmembers(module, lambda member: inspect.isclass(member))
        try:
            index = [name_and_class[0] for name_and_class in classes].index(name)
        except IndexError:
            raise IndexError(f"Unable to locate desired Operator {name} in provided Module {module.__name__}")
        return classes[index][1]


class JMetalPyWrapperTuned(JMetalPyWrapper):
    def construct(self, hyperparameters: Mapping, scenario: Mapping, warm_startup_info: Mapping) -> None:
        problem_init_params = HashableDict(scenario['problem_initialization_parameters'])
        problem = self._get_problem(scenario['Problem'], problem_init_params)
        self.load_initial_solutions(warm_startup_info, problem)

        from jmetal.operator.mutation import PermutationSwapMutation

        termination_criterion_cls = self._get_class_from_module(name=scenario["Budget"]["Type"], module=termination)
        termination_criterion = termination_criterion_cls(scenario["Budget"]["Amount"])

        mh_name = hyperparameters["low level heuristic"].split(".")[1]
        if mh_name == "GeneticAlgorithm":
            from jmetal.algorithm.singleobjective.genetic_algorithm import GeneticAlgorithm
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
            from jmetal.algorithm.singleobjective.simulated_annealing import SimulatedAnnealing
            self._llh_algorithm = SimulatedAnnealing(
                problem=problem,
                mutation=PermutationSwapMutation(0.8954537798654278),
                termination_criterion=termination_criterion,
                solution_generator=self._solution_generator
            )

        elif mh_name == "EvolutionStrategy":
            from jmetal.algorithm.singleobjective.evolution_strategy import EvolutionStrategy
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
    def construct(self, hyperparameters: Mapping, scenario: Mapping, warm_startup_info: Mapping) -> None:
        problem_init_params = HashableDict(scenario['problem_initialization_parameters'])
        problem = self._get_problem(scenario['Problem'], problem_init_params)
        self.load_initial_solutions(warm_startup_info, problem)

        from jmetal.operator.mutation import PermutationSwapMutation

        termination_criterion_cls = self._get_class_from_module(name=scenario["Budget"]["Type"], module=termination)
        termination_criterion = termination_criterion_cls(scenario["Budget"]["Amount"])

        mh_name = hyperparameters["low level heuristic"].split(".")[1]
        if mh_name == "GeneticAlgorithm":
            from jmetal.algorithm.singleobjective.genetic_algorithm import GeneticAlgorithm
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
            from jmetal.algorithm.singleobjective.simulated_annealing import SimulatedAnnealing
            self._llh_algorithm = SimulatedAnnealing(
                problem=problem,
                mutation=PermutationSwapMutation(0.5),
                termination_criterion=termination_criterion,
                solution_generator=self._solution_generator
            )

        elif mh_name == "EvolutionStrategy":
            from jmetal.algorithm.singleobjective.evolution_strategy import EvolutionStrategy
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
