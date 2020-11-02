import json
import os
from typing import Mapping

from worker_tools.hh.llh_runner import ILLHWrapper
from worker_tools.jar_runner import jar_runner


class JMetalWrapper(ILLHWrapper):

    def __init__(self):
        super().__init__()
        self._call_arguments = []

        self._call_arguments.append('binaries/jmetal-exec-5.8-jar-with-dependencies.jar')
        self._call_arguments.append('paths_to_stdout=True')
        self._initial_solutions_file_name = "warm_startup_solutions.txt"

    def construct(self, hyperparameters: Mapping, scenario: Mapping, warm_startup_info: Mapping) -> None:
        self._call_arguments.append(f"mutation_probability={hyperparameters.get('mutation_probability')}")
        self._call_arguments.append(f"elitist={hyperparameters.get('elitist')}")
        self._call_arguments.append(f"mu={hyperparameters.get('mu')}")
        self._call_arguments.append(f"lambda={hyperparameters.get('lambda_')}")

        scenario_file_name = scenario["problem_initialization_parameters"]["instance"].split("/")[-1]
        # Because of the framework implementation specifics, those TSP scenario files are 'embedded' into the jar file:
        # d15112.tsp
        # eil51.tsp
        # eil101.tsp
        # euclidA300.tsp
        # euclidB300.tsp
        # kroA100.tsp
        # kroA150.tsp
        # kroB100.tsp
        # kroB200.tsp
        # mona-lisa100K.tsp
        # pla7397.tsp
        # pr439.tsp
        # rat783.tsp
        # If one needs to add a new scenario, the jar file should be modified. TSP instances should be put into
        # tspInstances directory
        self._call_arguments.append(f"tsp_scenario=/tspInstances/{scenario_file_name}")

        self._attach_termination(scenario["Budget"])
        self._attach_initial_solutions(warm_startup_info)

    def run_and_report(self) -> Mapping:
        stdout, stderr, return_code = jar_runner(*self._call_arguments)

        # FW sends the output into stderr
        output = stderr.split("\n")

        if return_code != 0:
            self.logger.error(f"The return code after running the jMetal metaheuristic is not 0, but {return_code}.")
            self.logger.error("Output of run:")
            self.logger.error(output)
            result = {}
        else:
            # The output from jMetal heuristics is the regular output of solving process,
            # finalized with the desired report:
            # 1. final solutions paths
            # 2. the best solution objective value
            # 3. the improvement made (if no initial_solutions were, the improvement is 0)
            pointer = output.index("Paths START")
            solution_paths = []
            while True:
                pointer += 1
                if output[pointer] == "Paths END":
                    break
                else:
                    solution_paths.append(json.loads(output[pointer]))
            pointer += 2    # "Paths END" -> "Path length:" -> length value
            current_objective = float(output[pointer])
            pointer += 2    # length value -> "Improvement:" -> improvement value
            improvement = float(output[pointer])
            result = {
                "objective": current_objective,
                "improvement": improvement,
                "warm_startup_info": {
                    "paths": solution_paths
                }
            }

        # cleanup
        if os.path.exists(self._initial_solutions_file_name):
            os.remove(self._initial_solutions_file_name)

        return result

    def _attach_initial_solutions(self, warm_startup_info: Mapping) -> None:
        if warm_startup_info and 'paths' in warm_startup_info.keys():
            with open(self._initial_solutions_file_name, 'w') as f:
                for path in warm_startup_info['paths']:
                    f.write(json.dumps(path))
                    f.write("\n")
            self._call_arguments.append(f"initial_solutions={self._initial_solutions_file_name}")

    def _attach_termination(self, budget: Mapping) -> None:
        if budget["Type"] == "StoppingByTime":
            self._call_arguments.append(f"timeout_seconds={budget['Amount']}")
        else:
            raise TypeError("Termination based not on time is not supported yet.")


class JMetalWrapperTuned(JMetalWrapper):
    def construct(self, hyperparameters: Mapping, scenario: Mapping, warm_startup_info: Mapping) -> None:
        self._call_arguments.append("mutation_probability=0.9938884974393134")
        self._call_arguments.append("elitist=True")
        self._call_arguments.append("mu=5")
        self._call_arguments.append("lambda=605")

        scenario_file_name = scenario["problem_initialization_parameters"]["instance"].split("/")[-1]
        self._call_arguments.append(f"tsp_scenario=/tspInstances/{scenario_file_name}")

        self._attach_termination(scenario["Budget"])
        self._attach_initial_solutions(warm_startup_info)


class JMetalWrapperDefault(JMetalWrapper):
    def construct(self, hyperparameters: Mapping, scenario: Mapping, warm_startup_info: Mapping) -> None:
        self._call_arguments.append("mutation_probability=0.5")
        self._call_arguments.append("elitist=False")
        self._call_arguments.append("mu=500")
        self._call_arguments.append("lambda=500")

        scenario_file_name = scenario["problem_initialization_parameters"]["instance"].split("/")[-1]
        self._call_arguments.append(f"tsp_scenario=/tspInstances/{scenario_file_name}")

        self._attach_termination(scenario["Budget"])
        self._attach_initial_solutions(warm_startup_info)
