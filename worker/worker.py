import logging


def hpps_java_so_simulator(task: dict):
    import subprocess
    import sys
    import os
    import json

    logger = logging.getLogger(__name__)

    strategy = task["parameters"]["Strategy"]

    if strategy == "cpr":
        duration = task["parameters"]["duration"]
        setup_needed = task["parameters"]["setup_needed"]
        direct_successor_count = task["parameters"]["direct_successor_count"]
        direct_successor_sum_max_processing_time = task["parameters"]["direct_successor_sum_max_processing_time"]
        direct_successor_sum_min_processing_time = task["parameters"]["direct_successor_sum_min_processing_time"]
        project_finish_time = task["parameters"]["project_finish_time"]
        project_start_time = task["parameters"]["project_start_time"]
        resources = task["parameters"]["resources"]
        setup_time = task["parameters"]["setup_time"]
        total_successor_count = task["parameters"]["total_successor_count"]
        total_successor_sum_max_processing_time = task["parameters"]["total_successor_sum_max_processing_time"]
        total_successor_sum_min_processing_time = task["parameters"]["total_successor_sum_min_processing_time"]
        waiting_job_count = task["parameters"]["waiting_job_count"]
        waiting_time = task["parameters"]["waiting_time"]

        data = []
        data.append({
            "name" : "duration",
            "value": duration
        })
        data.append({
            "name" : "setup_needed",
            "value": setup_needed
        })
        data.append({
            "name" : "direct_successor_count",
            "value": direct_successor_count
        })
        data.append({
            "name": "direct_successor_sum_max_processing_time",
            "value": direct_successor_sum_max_processing_time
        })
        data.append({
            "name": "direct_successor_sum_min_processing_time",
            "value": direct_successor_sum_min_processing_time
        })
        data.append({
            "name": "project_finish_time",
            "value": project_finish_time
        })
        data.append({
            "name": "project_start_time",
            "value": project_start_time
        })
        data.append({
            "name": "resources",
            "value": resources
        })
        data.append({
            "name": "setup_time",
            "value": setup_time
        })
        data.append({
            "name": "total_successor_count",
            "value": total_successor_count
        })
        data.append({
            "name": "total_successor_sum_max_processing_time",
            "value": total_successor_sum_max_processing_time
        })
        data.append({
            "name": "total_successor_sum_min_processing_time",
            "value": total_successor_sum_min_processing_time
        })
        data.append({
            "name": "waiting_job_count",
            "value": waiting_job_count
        })
        data.append({
            "name": "waiting_time",
            "value": waiting_time
        })
        with open('scenarios/hpps/cpr.json', 'w') as outfile:
           json.dump(data, outfile)

        command = "java -jar binaries/hpps/hybridpps.jar scenarios/hpps/{} -c scenarios/hpps/cpr.json".\
            format(task["Scenario"]["problem_initialization_parameters"]["instance"])
    else:
        command = "java -jar binaries/hpps/hybridpps.jar scenarios/hpps/{0} -s {1}".\
            format(task["Scenario"]["problem_initialization_parameters"]["instance"], task["parameters"]["Strategy"])

    try:
        retcode = subprocess.call(command, shell=True)
        if retcode < 0:
            logger.info("Java code was terminated by signal", -retcode, file=sys.stderr)
        else:
            logger.info("Java code returned", retcode, file=sys.stderr)
    except OSError as e:
        logger.error("Execution failed:", e, file=sys.stderr)

    import re
    find_date = re.compile(r".*-(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\d+).*")
    latest_result = ""
    latest_date = []
    for file in os.listdir("."):
        split_date = find_date.findall(file)
        if len(split_date) == 0:
            continue
        else:
            if latest_result == "":
                latest_result = file
                latest_date = split_date
            else:
                if latest_date < split_date:
                    latest_result = file
                    latest_date = split_date

    avg_makespan = 0
    with open(latest_result) as file:
        data = json.load(file)
        results = data[0]["strategies"][0]["results"]
        from functools import reduce

        avg_makespan = reduce(lambda a, b: a + b, results) / len(results)

    return {"makespan": avg_makespan}


def energy_consumption(task: dict):
    from random import choice

    from worker_tools.splitter import Splitter

    try:
        data = Splitter("scenarios/energy_consumption/" + task['Scenario']['ws_file'])
        data.search(str(task['parameters']['frequency']), str(task['parameters']['threads']))
        result = choice(data.new_data)
        return {
            'energy': float(result["EN"]),
            'time': float(result['TIM'])
        }
    except Exception as error:
        logging.getLogger(__name__).error(
            "An error occurred during performing 'energy_consumption' Task with parameters %s: %s" % (
                task['parameters'], error), exc_info=True)

def genetic(task: dict):
    import os
    import subprocess
    import sys
    from random import choice

    from worker_tools.splitter import Splitter

    logger = logging.getLogger(__name__)
    try:
        generations = str(task['parameters']['generations'])
        populationSize = str(task['parameters']['populationSize'])
        numTopLevelComponents = str(task['Scenario']['numTopLevelComponents'])
        avgNumImplSubComponents = str(task['Scenario']['avgNumImplSubComponents'])
        implSubComponentStdDerivation = str(task['Scenario']['implSubComponentStdDerivation'])
        avgNumCompSubComponents = str(task['Scenario']['avgNumCompSubComponents'])
        compSubComponentStdDerivation = str(task['Scenario']['compSubComponentStdDerivation'])
        componentDepth = str(task['Scenario']['componentDepth'])
        numImplementations = str(task['Scenario']['numImplementations'])
        excessComputeResourceRatio = str(task['Scenario']['excessComputeResourceRatio'])
        numRequests = str(task['Scenario']['numRequests'])
        numCpus = str(task['Scenario']['numCpus'])
        seed = str(task['Scenario']['seed'])
        timeoutValue = str(task['Scenario']['timeoutValue'])
        timeoutUnit = str(task['Scenario']['timeoutUnit'])
        ##
        treeMutateOperatorP = str(task['parameters']['treeMutateOperatorP'])
        treeMutateOperatorP1 = str(task['parameters']['treeMutateOperatorP1'])
        treeMutateOperatorP2 = str(task['parameters']['treeMutateOperatorP2'])
        treeMutateOperatorP3 = str(task['parameters']['treeMutateOperatorP3'])
        ##
        ###
        Lambda = str(task['parameters']['lambda_'])
        crossoverRate = str(task['parameters']['crossoverRate'])
        mu = str(task['parameters']['mu'])
        tournament = str(task['parameters']['tournament'])
        ###

        ws_file = "result_v{}_q{}_d{}_r{}.csv". \
            format(numImplementations, numRequests, componentDepth, excessComputeResourceRatio)

        file_name = "results/scenarios/" + ws_file

        command = (
            "java -jar binaries/jastadd-mquat-solver-genetic-2.0.0-SNAPSHOT.jar \
                %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s"
            % (numTopLevelComponents, avgNumImplSubComponents, implSubComponentStdDerivation,
                avgNumCompSubComponents,
                compSubComponentStdDerivation, componentDepth, numImplementations, excessComputeResourceRatio,
                numRequests,
                numCpus, seed, timeoutValue, timeoutUnit, ws_file, generations, populationSize,
                treeMutateOperatorP, treeMutateOperatorP1, treeMutateOperatorP2, treeMutateOperatorP3,
                Lambda, crossoverRate, mu, tournament))
        try:
            retcode = subprocess.call(command, shell=True)
            if retcode < 0:
                logger.info("Java code was terminated by signal", -retcode, file=sys.stderr)
            else:
                logger.info("Java code returned", retcode, file=sys.stderr)
        except OSError as error:
            logger.error("Execution failed:", error, file=sys.stderr)

        if os.path.exists(file_name):
            data = Splitter(file_name)
            data.searchGA(file_name)
            result = choice(data.new_data)
            return {
                'Validity': int(result["Validity"])
            }
        else:
            logger.error("java command: %s doesnt create result file" % command)
            raise Exception("java command: %s doesnt create result file" % command)
    except Exception as error:
        logger.error(f"An error occurred during performing 'genetic' Task with parameters {task['parameters']}: {error}")
    return {
        'Validity': 'NaN'
    }


def simulatedAnnealing(task: dict):
    import os
    import subprocess
    import sys
    from random import choice

    from worker_tools.splitter import Splitter

    logger = logging.getLogger(__name__)
    try:
        # params
        subComponentUnassignedFactor = str(task['parameters']['subComponentUnassignedFactor'])
        softwareComponentUnassignedFactor = str(task['parameters']['softwareComponentUnassignedFactor'])
        hardScoreStartingTemperaturePercentage = str(task['parameters']['hardScoreStartingTemperaturePercentage'])
        softScoreStartingTemperaturePercentage = str(task['parameters']['softScoreStartingTemperaturePercentage'])
        acceptedCountLimit = str(task['parameters']['acceptedCountLimit'])
        millisecondsSpentLimit = str(task['parameters']['millisecondsSpentLimit'])
        unimprovedMillisecondsSpentLimit = str(task['parameters']['unimprovedMillisecondsSpentLimit'])

        # scenario

        ws_file = str(task['Scenario']['ws_file'])
        numTopLevelComponents = str(task['Scenario']['numTopLevelComponents'])
        avgNumImplSubComponents = str(task['Scenario']['avgNumImplSubComponents'])
        implSubComponentStdDerivation = str(task['Scenario']['implSubComponentStdDerivation'])
        avgNumCompSubComponents = str(task['Scenario']['avgNumCompSubComponents'])
        compSubComponentStdDerivation = str(task['Scenario']['compSubComponentStdDerivation'])
        componentDepth = str(task['Scenario']['componentDepth'])
        numImplementations = str(task['Scenario']['numImplementations'])
        excessComputeResourceRatio = str(task['Scenario']['excessComputeResourceRatio'])
        numRequests = str(task['Scenario']['numRequests'])
        numCpus = str(task['Scenario']['numCpus'])
        seed = str(task['Scenario']['seed'])
        # file_name = "result_v{}_q{}_d{}_r{}.csv".\
        #     format(numImplementations, numRequests, componentDepth, excessComputeResourceRatio.replace('.', '_'))
        command = (
            "java -jar binaries/jastadd-mquat-solver-mh-1.0-SNAPSHOT.jar \
                %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s"
            % (subComponentUnassignedFactor, softwareComponentUnassignedFactor,
                hardScoreStartingTemperaturePercentage, softScoreStartingTemperaturePercentage,
                acceptedCountLimit, millisecondsSpentLimit, unimprovedMillisecondsSpentLimit,

                numTopLevelComponents, avgNumImplSubComponents, implSubComponentStdDerivation,
                avgNumCompSubComponents, compSubComponentStdDerivation, componentDepth, numImplementations,
                excessComputeResourceRatio, numRequests, numCpus, seed))

        try:
            retcode = subprocess.call(command, shell=True)
            if retcode < 0:
                logger.info("Java code was terminated by signal", -retcode, file=sys.stderr)
            else:
                logger.info("Java code returned", retcode, file=sys.stderr)
        except OSError as e:
            logger.error("Execution failed:", e, file=sys.stderr)

        logger.debug(ws_file)
        if os.path.exists(ws_file):
            data = Splitter(ws_file)
            logger.debug("splitter OK")
            data.searchSA(ws_file)
            logger.debug("search sa ok")
            result = choice(data.new_data)
            return {
                'hardScoreImprovement': float(result["hardScoreImprovement"]),
                'softScoreImprovement': float(result["softScoreImprovement"])
            }
        else:
            raise Exception("java command: %s didn't create result file" % command)
    except Exception:
        logger.error("ERROR IN WORKER during performing SA with parameters: %s" % task['parameters'])
    return {
        'hardScoreImprovement': 'NaN',
        'softScoreImprovement': 'NaN'
    }


def synthetic_problems(task: dict):
    import math
    import random as rd
    func = task["Scenario"].get('function name', None)
    if func == "ackley":
        x = task["parameters"]['x']
        y = task["parameters"]['y']
        part_1 = -0.2 * math.sqrt(0.5 * (math.pow(x, 2) + math.pow(y, 2)))
        part_2 = 0.5 * (math.cos(2 * math.pi * x) + math.cos(2 * math.pi * y))
        result = -20 * math.exp(part_1) - math.exp(part_2) + math.exp(1) + 20
    elif func == "himmelblau":
        x = task["parameters"]['x']
        y = task["parameters"]['y']
        result = math.pow(math.pow(x, 2) + y + 11, 2) + math.pow(x + math.pow(y, 2) - 7, 2)
    else:
        raise TypeError(f"Unknown function name specified in scenario: {task['Scenario']}")
    deviation = task["Scenario"].get('deviation, %', 0)
    result = rd.gauss(mu=result, sigma=result * deviation / 100)
    return {"result": result}


def tsp_hh(task: dict):
    from worker_tools.hh.llh_runner import LLHRunner

    framework = task["parameters"]["low level heuristic"].split(".")[0]

    if framework == "jMetalPy":
        # Trick to force the meta-heuristic use only a default, or tuned parameters.
        if task["Scenario"]["Hyperparameters"] == 'default':
            from worker_tools.hh.llh_wrapper_jmetalpy import \
                JMetalPyWrapperDefault as LLH_Wrapper
        elif task["Scenario"]["Hyperparameters"] == 'tuned':
            from worker_tools.hh.llh_wrapper_jmetalpy import \
                JMetalPyWrapperTuned as LLH_Wrapper
        else:
            # use provided hyperparameters
            from worker_tools.hh.llh_wrapper_jmetalpy import \
                JMetalPyWrapper as LLH_Wrapper

    elif framework == "jMetal":
        if task["Scenario"]["Hyperparameters"] == 'default':
            from worker_tools.hh.llh_wrapper_jmetal import \
                JMetalWrapperDefault as LLH_Wrapper
        elif task["Scenario"]["Hyperparameters"] == 'tuned':
            from worker_tools.hh.llh_wrapper_jmetal import \
                JMetalWrapperTuned as LLH_Wrapper
        else:
            from worker_tools.hh.llh_wrapper_jmetal import \
                JMetalWrapper as LLH_Wrapper
    else:
        raise TypeError(f"Unknown framework: {framework}")

    llh_runner = LLHRunner(task, LLH_Wrapper())
    llh_runner.build()
    llh_runner.execute()
    return llh_runner.report
