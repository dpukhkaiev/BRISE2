import logging


def test_tsp_hh(task: dict) -> dict:
    """
    Stub for testing the hyper-heuristic LLH selection logic.
    To use this stub - import it into worker/worker.py module and set
    in experiment's description.TaskConfiguration.TaskName "test_tsp_hh".

    The principle is following: depending on the heuristic name, specified in task and iteration counter (simulates
    the RL process), stub returns improvement in a solution quality.

    For instance, currently it is specified that if the task is to run jMetalPy.SimulatedAnnealing, the improvement
    would be in random range from 0.9 to 1.2 (some abstract points), but if jMetalPy.EvolutionStrategy is specified,
    the improvement will be higher (1.3 ... 2.3). Thus, LLH selection strategy after a couple of tasks should
    find out, that jMetalPy.EvolutionStrategy is better config than SimulatedAnnealing and use it more frequently.

    Simultaneously, since SimulatedAnnealing and GeneticAlgorithm are of the same quality, ideally, they should be
    selected with the same frequency, while jMetal.EvolutionStrategy just a little bit more frequently (or negligibly).
    :param task:
    :return:
    """
    logging.getLogger("jMetalPy Stub").info(task)
    import math
    import random as rd

    def result_in_iteration(i, b):
        base_result = 3000000
        return base_result - sum((b * 100000/math.exp(x / 10) for x in range(i)))

    mh_name = task["parameters"]["low level heuristic"]
    iteration = task['parameter_control_info']['iteration'] if 'iteration' in task['parameter_control_info'].keys() else 0
    # by changing the boost, the favor should move from one MH to another.
    if mh_name == 'jMetalPy.SimulatedAnnealing':
        boost = rd.uniform(0.9, 1.2)
    elif mh_name == "jMetalPy.GeneticAlgorithm":
        boost = rd.uniform(0.9, 1.2)
    elif mh_name == "jMetalPy.EvolutionStrategy":
        boost = rd.uniform(1.3, 2.3)
    elif mh_name == "jMetal.EvolutionStrategy":
        boost = rd.uniform(0.9, 1.3)
    else:
        raise TypeError("Wrong MH")

    current_result = result_in_iteration(iteration, boost)
    previous_result = result_in_iteration(iteration - 1, boost)
    result = {
        "objective": current_result,
        "improvement": (previous_result - current_result) / previous_result,
        "parameter_control_info": {
            "iteration": iteration + 1
        }
    }
    return result
