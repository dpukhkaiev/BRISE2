import logging


def test(task: dict):
    import random
    return {'Y1': random.random(), 'Y2': random.random(), 'Y3': random.random(), 'Y4': random.random(), 'Y5': random.random()}


def energy_consumption(task: dict):
    from random import choice
    from worker_tools.splitter import Splitter

    frequency_parameter_mapping = {
        "Context.SearchSpace.frequency.twelve_hundred_hertz": "1200.0",
        "Context.SearchSpace.frequency.thirteen_hundred_hertz": "1300.0",
        "Context.SearchSpace.frequency.fourteen_hundred_hertz": "1400.0",
        "Context.SearchSpace.frequency.sixteen_hundred_hertz": "1600.0",
        "Context.SearchSpace.frequency.seventeen_hundred_hertz": "1700.0",
        "Context.SearchSpace.frequency.eighteen_hundred_hertz": "1800.0",
        "Context.SearchSpace.frequency.nineteen_hundred_hertz": "1900.0",
        "Context.SearchSpace.frequency.twenty_hundred_hertz": "2000.0",
        "Context.SearchSpace.frequency.twenty_two_hundred_hertz": "2200.0",
        "Context.SearchSpace.frequency.twenty_three_hundred_hertz": "2300.0",
        "Context.SearchSpace.frequency.twenty_four_hundred_hertz": "2400.0",
        "Context.SearchSpace.frequency.twenty_five_hundred_hertz": "2500.0",
        "Context.SearchSpace.frequency.twenty_seven_hundred_hertz": "2700.0",
        "Context.SearchSpace.frequency.twenty_eight_hundred_hertz": "2800.0",
        "Context.SearchSpace.frequency.twenty_nine_hundred_hertz": "2900.0",
        "Context.SearchSpace.frequency.turbo": "2901.0",
    }

    threads_parameter_mapping = {
        "Context.SearchSpace.threads.one": "1",
        "Context.SearchSpace.threads.two": "2",
        "Context.SearchSpace.threads.four": "4",
        "Context.SearchSpace.threads.eight": "8",
        "Context.SearchSpace.threads.sixteen": "16",
        "Context.SearchSpace.threads.thirty_two": "32",
    }

    try:
        logging.info(task['parameters']['frequency'])
        data = Splitter("scenarios/energy_consumption/" + task['Scenario']['ws_file'])
        data.search(frequency_parameter_mapping[task['parameters']['frequency']],
                    threads_parameter_mapping[task['parameters']['threads']])
        result = choice(data.new_data)
        return {
            'energy': float(result["EN"]),
            'time': float(result['TIM'])
        }
    except Exception as error:
        logging.getLogger(__name__).error(
            "An error occurred during performing 'energy_consumption' Task with parameters %s: %s" % (
                task['parameters'], error), exc_info=True)


def naiveBayes_mock(task: dict):
    from random import choice
    from worker_tools.mock_values_corrector import correct_values
    from worker_tools.splitter import Splitter
    try:
        bandwidth_selection = str(task['parameters']['bandwidth_selection']).split(".")[-1]
    except:
        bandwidth_selection = "None"
    try:
        application_grid_size = task['parameters']['application_grid_size']
    except:
        application_grid_size = "None"
    try:
        minimum_bandwidth = task['parameters']['minimum_bandwidth']
    except:
        minimum_bandwidth = "None"
    try:
        number_of_kernels = task['parameters']['number_of_kernels']
    except:
        number_of_kernels = "None"
    try:
        data = Splitter("scenarios/rapid_miner/" + task['Scenario']['ws_file'])
        # Only for demo!
        # To enable mock data to be used, real values of continuous parameters must be discretized
        corrected_bandwidth, corrected_min_bandwidth, corrected_num_kernels, corrected_app_grid_size = \
            correct_values(task['parameters']['bandwidth'],
                           minimum_bandwidth,
                           number_of_kernels,
                           application_grid_size)
        data.searchNB(str(task['parameters']['laplace_correction']).split(".")[-1],
                      str(task['parameters']['estimation_mode']).split(".")[-1],
                      bandwidth_selection,
                      str(corrected_bandwidth),
                      str(corrected_min_bandwidth),
                      str(corrected_num_kernels),
                      str(task['parameters']['use_application_grid']).split(".")[-1],
                      str(corrected_app_grid_size))
        result = choice(data.new_data)
        logging.warning(result["PREC_AT_99_REC"])
        return {
            'PrecisionAtNinentyNineRecall': float(result["PREC_AT_99_REC"])
        }
    except Exception as error:
        logging.getLogger(__name__).error(f"An error occurred during performing 'taskNB' (NaiveBayes mock) "
                                          f"Task with parameters {task['parameters']}: {error}")
    return {
        'PrecisionAtNinentyNineRecall': 'NaN'
    }


def naiveBayes(task: dict):
    from worker_tools.rm_script import insert_config_to_RM_process, run_RM

    """Initialization function to run NaiveBayes algorithm inside RapidMiner
    :param task:dict: current task, generated by WorkerServiceClient
    :rtype:float: average value of precision and recall
    """
    logger = logging.getLogger(__name__)
    # initialize all required pathes
    try:
        algorithm = 'NAIVE_BAYES'
        RMrepository = '//ServerRepository/NaiveBayes/'
        path2process = '/home/w_user/.RapidMiner/repositories/ServerRepository/NaiveBayes/MA_EXR_1_EX_1_NB_INV.rmp'
        path2result = './scenarios/rapid_miner/NB_performance.csv'
        path2RM = '/home/w_user/rapidminer-studio/scripts/rapidminer-batch.sh'

        from worker_tools.params_to_string import params_to_string
        task = params_to_string(task)

        RMprocess = insert_config_to_RM_process(algorithm, task['parameters'], path2process)
    except Exception as error:
        logger.error(f"An error occurred during performing NaiveBayes Task with parameters {task['parameters']}: {error}")
    return run_RM(path2RM, RMrepository, RMprocess, path2result)


def randomForest(task: dict):
    from worker_tools.rm_script import insert_config_to_RM_process, run_RM

    """Initialization function to run RandomForest algorithm inside RapidMiner
    :param task:dict: task with current measured configuration of RandomForest in a {key:value} format
    :rtype:float: average value of precision and recall
    """
    logger = logging.getLogger(__name__)
    # initialize all required pathes
    try:
        # use RapidMiner Automodel to define default config, if it is specified:
        automodel_default = True if "defined_by_automodel" in task['parameters'].values() else False
        if automodel_default is True:
            algorithm = 'AUTO_MODEL'
            RMrepository = '//ServerRepository/Automodel/'
            path2process = '/home/w_user/.RapidMiner/repositories/ServerRepository/Automodel/Autommod.rmp'
        else:
            algorithm = 'RANDOM_FOREST'
            RMrepository = '//ServerRepository/RandomForest/'
            path2process = '/home/w_user/.RapidMiner/repositories/ServerRepository/RandomForest/MA_EXR_1_EX_2_RF_INV.rmp'
        path2result = './scenarios/rapid_miner/RF_performance.csv'
        path2RM = '/home/w_user/rapidminer-studio/scripts/rapidminer-batch.sh'

        from worker_tools.params_to_string import params_to_string
        task = params_to_string(task)

        RMprocess = insert_config_to_RM_process(algorithm, task['parameters'], path2process)
    except Exception as error:
        logger.error(f"An error occurred during performing RandomForest Task with parameters {task['parameters']}: "
                     f"{error}")
    return run_RM(path2RM, RMrepository, RMprocess, path2result)


def neuralNet(task: dict):
    from worker_tools.rm_script import insert_config_to_RM_process, run_RM

    """Initialization function to run NeuralNet algorithm inside RapidMiner
    :param task:dict: task with current measured configuration of NeuralNet in a {key:value} format
    :rtype:float: average value of precision and recall
    """
    logger = logging.getLogger(__name__)
    # initialize all required pathes
    try:
        algorithm = 'NEURAL_NET'
        RMrepository = '//ServerRepository/NeuralNetwork/'
        path2process = '/home/w_user/.RapidMiner/repositories/ServerRepository/NeuralNetwork/MA_EXR_1_EX_3_NN_INV.rmp'
        path2result = './scenarios/rapid_miner/NN_performance.csv'
        path2RM = '/home/w_user/rapidminer-studio/scripts/rapidminer-batch.sh'

        from worker_tools.params_to_string import params_to_string
        task = params_to_string(task)

        RMprocess = insert_config_to_RM_process(algorithm, task['parameters'], path2process)
    except Exception as error:
        logger.error(f"An error occurred during performing NeuralNet Task with parameters {task['parameters']}: {error}")
    return run_RM(path2RM, RMrepository, RMprocess, path2result)


def SVM(task: dict):
    from worker_tools.rm_script import insert_config_to_RM_process, run_RM

    """Initialization function to run Support Vector Machine (SVM) algorithm inside RapidMiner
    :param task:dict: task with current measured configuration of Support Vector Machine (SVM) in a {key:value} format
    :rtype:float: average value of precision and recall
    """
    logger = logging.getLogger(__name__)
    # initialize all required pathes
    try:
        algorithm = 'SUPPORT_VECTOR_MACHINE'
        RMrepository = '//ServerRepository/SVM/'
        path2process = '/home/w_user/.RapidMiner/repositories/ServerRepository/SVM/MA_EXR_1_EX_4_SVM_INV.rmp'
        path2result = './scenarios/rapid_miner/SVM_performance.csv'
        path2RM = '/home/w_user/rapidminer-studio/scripts/rapidminer-batch.sh'

        from worker_tools.params_to_string import params_to_string
        task = params_to_string(task)

        RMprocess = insert_config_to_RM_process(algorithm, task['parameters'], path2process)
    except Exception as error:
        logger.error(f"An error occurred during performing SVM Task with parameters {task['parameters']}: {error}")
    return run_RM(path2RM, RMrepository, RMprocess, path2result)


def genetic(task: dict):
    import os
    import subprocess
    import sys
    from random import choice

    from worker_tools.splitter import Splitter

    logger = logging.getLogger(__name__)
    try:
        generations = str(task['parameters']['generations'])
        population_size = str(task['parameters']['population_size'])
        num_top_level_components = str(task['Scenario']['numTopLevelComponents'])
        avg_num_impl_sub_components = str(task['Scenario']['avgNumImplSubComponents'])
        impl_sub_component_std_derivation = str(task['Scenario']['implSubComponentStdDerivation'])
        avg_num_comp_sub_components = str(task['Scenario']['avgNumCompSubComponents'])
        comp_sub_component_std_derivation = str(task['Scenario']['compSubComponentStdDerivation'])
        component_depth = str(task['Scenario']['componentDepth'])
        num_implementations = str(task['Scenario']['numImplementations'])
        excess_compute_resource_ratio = str(task['Scenario']['excessComputeResourceRatio'])
        num_requests = str(task['Scenario']['numRequests'])
        num_cpus = str(task['Scenario']['numCpus'])
        seed = str(task['Scenario']['seed'])
        timeout_value = str(task['Scenario']['timeoutValue'])
        timeout_unit = str(task['Scenario']['timeoutUnit'])

        lambda_ = str(task['parameters']['lambda_'])
        crossover_rate = str(task['parameters']['crossover_rate'])
        mu = str(task['parameters']['mu'])
        ###
        selector_type = str(task['parameters']['selector_type']).split(".")[-1]
        mutation_rate = str(task['parameters']['mutation_rate'])
        resources_mutation_probability = str(task['parameters']['resources_mutation_probability'])
        evaluator_validity_weight = str(task['parameters']['evaluator_validity_weight'])
        evaluator_software_validity_weight = str(task['parameters']['evaluator_software_validity_weight'])
        random_software_assignment_attempts = str(task['parameters']['random_software_assignment_attempts'])
        populate_software_solution_attempts = str(task['parameters']['populate_software_solution_attempts'])
        ws_file = "result_v{}_q{}_d{}_r{}.csv". \
            format(num_implementations, num_requests, component_depth, excess_compute_resource_ratio)

        file_name = "results/scenarios/" + ws_file

        command = (
            "java -jar binaries/jastadd-mquat-solver-genetic-2.0.0-SNAPSHOT.jar \
                %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s"
            % (num_top_level_components, avg_num_impl_sub_components, impl_sub_component_std_derivation,
               avg_num_comp_sub_components, comp_sub_component_std_derivation, component_depth, num_implementations,
               excess_compute_resource_ratio, num_requests, num_cpus, seed, timeout_value, timeout_unit, ws_file,
               generations, selector_type, population_size, lambda_, crossover_rate, mu, mutation_rate,
               resources_mutation_probability, evaluator_validity_weight, evaluator_software_validity_weight,
               random_software_assignment_attempts, populate_software_solution_attempts))
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

    map_millisecondsSpentLimit = {"Context.SearchSpace.millisecondsSpentLimit.tenthousand": 10000}
    map_unimprovedMillisecondsSpentLimit = {"Context.SearchSpace.unimprovedMillisecondsSpentLimit.tenthousand": 10000}
    try:
        # params
        subComponentUnassignedFactor = str(task['parameters']['subComponentUnassignedFactor'])
        softwareComponentUnassignedFactor = str(task['parameters']['softwareComponentUnassignedFactor'])
        hardScoreStartingTemperaturePercentage = str(task['parameters']['hardScoreStartingTemperaturePercentage'])
        softScoreStartingTemperaturePercentage = str(task['parameters']['softScoreStartingTemperaturePercentage'])
        acceptedCountLimit = str(task['parameters']['acceptedCountLimit'])
        millisecondsSpentLimit = map_millisecondsSpentLimit[str(task['parameters']['millisecondsSpentLimit'])]
        unimprovedMillisecondsSpentLimit = map_unimprovedMillisecondsSpentLimit[
            str(task['parameters']['unimprovedMillisecondsSpentLimit'])]

        # scenario

        # ws_file = str(task['Scenario']['ws_file'])
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
        ws_file = "result_v{}_q{}_d{}_r{}.csv".\
            format(numImplementations, numRequests, componentDepth, excessComputeResourceRatio.replace('.', '_'))
        command = (
            "java -jar binaries/jastadd-mquat-solver-mh-1.0-SNAPSHOT.jar \
                %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s"
            % (subComponentUnassignedFactor, softwareComponentUnassignedFactor,
                hardScoreStartingTemperaturePercentage, softScoreStartingTemperaturePercentage,
                acceptedCountLimit, millisecondsSpentLimit, unimprovedMillisecondsSpentLimit,
                numTopLevelComponents, avgNumImplSubComponents, implSubComponentStdDerivation,
                avgNumCompSubComponents, compSubComponentStdDerivation, componentDepth, numImplementations,
                excessComputeResourceRatio, numRequests, numCpus, seed))

        logger.warning("Starting for %s", ws_file)

        try:
            retcode = subprocess.call(command, shell=True)
            if retcode < 0:
                logger.info("Java code was terminated by signal", -retcode, file=sys.stderr)
            else:
                logger.info("Java code returned", retcode, file=sys.stderr)
        except OSError as e:
            logger.error("Execution failed:", e, file=sys.stderr)

        logger.warning(ws_file)
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
    func = task["Scenario"]["function_name"]
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
    deviation = task["Scenario"]["deviation"]
    result = rd.gauss(mu=result, sigma=result * deviation / 100)
    return {"result": result}


def tsp_hh(task: dict):
    from worker_tools.hh.llh_runner import LLHRunner
    logging.warning(task)
    framework = "jMetalPy" if "jMetalPy" in task["parameters"]["LLH"] else "jMetal"

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


def hh(task: dict):
    from worker_tools.hh.llh_runner import LLHRunner

    framework = "jMetalPy" if "jMetalPy" in task["parameters"]["LLH"] else "jMetal"

    if framework == "jMetalPy":
        if task["Scenario"]["Hyperparameters"] == 'default':
            from worker_tools.hh.llh_wrapper_jmetalpy import JMetalPyWrapperDefault as LLH_Wrapper
        elif task["Scenario"]["Hyperparameters"] == 'tuned':
            from worker_tools.hh.llh_wrapper_jmetalpy import JMetalPyWrapperTuned as LLH_Wrapper
        else:
            # use provided hyperparameters
            from worker_tools.hh.llh_wrapper_jmetalpy import JMetalPyWrapper as LLH_Wrapper

    elif framework == "jMetal":
        if task["Scenario"]["Hyperparameters"] == 'default':
            from worker_tools.hh.llh_wrapper_jmetal import JMetalWrapperDefault as LLH_Wrapper
        elif task["Scenario"]["Hyperparameters"] == 'tuned':
            from worker_tools.hh.llh_wrapper_jmetal import JMetalWrapperTuned as LLH_Wrapper
        else:
            from worker_tools.hh.llh_wrapper_jmetal import JMetalWrapper as LLH_Wrapper
    else:
        raise TypeError(f"Unknown framework: {framework}")

    llh_runner = LLHRunner(task, LLH_Wrapper(problem_type=task["Scenario"]["problem_type"]))
    llh_runner.build()
    llh_runner.execute()
    return llh_runner.report


def openml_RF_sklearn(task: dict):
    import openml
    import numpy as np
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import cross_validate

    # import a dataset from openml
    dataset = openml.datasets.get_dataset(task["Scenario"]["DatasetID"])
    X, y, _, _ = dataset.get_data(dataset_format="array", target=dataset.default_target_attribute)
    criterion_parameter_mapping = {
        "Context.SearchSpace.criterion.gini": "gini",
        "Context.SearchSpace.criterion.entropy": "entropy"
    }
    max_features_parameter_mapping = {
        "Context.SearchSpace.criterion.gini.max_features.sqrt": "sqrt",
        "Context.SearchSpace.criterion.entropy.max_features.sqrt": "sqrt",
        "Context.SearchSpace.criterion.gini.max_features.log2": "log2",
        "Context.SearchSpace.criterion.entropy.max_features.log2": "log2"
    }
    # Build sklearn RF pipeline
    clf = make_pipeline(StandardScaler(),
                        RandomForestClassifier(criterion=criterion_parameter_mapping[task["parameters"]["criterion"]],
                                               max_depth=task["parameters"]["max_depth"],
                                               max_features=max_features_parameter_mapping[
                                                   task["parameters"]["max_features"]],
                                               min_samples_leaf=task["parameters"]["min_samples_leaf"],
                                               min_samples_split=task["parameters"]["min_samples_split"],
                                               n_estimators=task["parameters"]["n_estimators"]))

    # evaluate classifier with cross_validation
    scores = cross_validate(clf, X, y,
                            scoring=["f1_macro", "f1_weighted", "roc_auc"],
                            cv=5,
                            n_jobs=-1)
    fit_time = np.mean(scores["fit_time"])
    test_f1_macro = np.mean(scores["test_f1_macro"])
    test_f1_weighted = np.mean(scores["test_f1_weighted"])
    test_roc_auc = np.mean(scores["test_roc_auc"])

    result = {
        "fit_time": fit_time,
        "test_f1_macro": test_f1_macro,
        "test_f1_weighted": test_f1_weighted,
        "test_roc_auc": test_roc_auc
    }
    return result


def moo_benchmarks(task: dict):
    import pygmo as pg
    import numpy as np
    logging.warning(task)
    keys = task['Scenario']['BenchmarkSuite'].keys()
    suite = list(filter(lambda x: x != "problemID", keys))[0]

    problem_id = int(task['Scenario']['ProblemID'])
    number_of_dimensions = len(task['parameters'])
    number_of_objectives = len(task['result_structure'])
    logging.warning("number_of_dimensions: " + str(number_of_dimensions))
    logging.warning("number_of_objectives: " + str(number_of_objectives))

    if suite == "WFG":
        user_defined_problem = pg.wfg(prob_id=problem_id, dim_dvs=number_of_dimensions, dim_obj=number_of_objectives,
                                      dim_k=task['Scenario']['BenchmarkSuite']['WFG']['PositionRelatedParameters'])

    elif suite == "ZDT":
        user_defined_problem = pg.zdt(prob_id=problem_id, param=number_of_dimensions)
    elif suite == "DTLZ":
        user_defined_problem = pg.dtlz(prob_id=problem_id, dim=number_of_dimensions, fdim=number_of_objectives)

    problem = pg.problem(user_defined_problem)

    parameters = np.array(list(task['parameters'].values()), dtype=np.float64)
    result = problem.fitness(parameters)
    logging.warning('f1: ' + str(result[0]) + 'f2: ' + str(result[1]))
    return {
        'f1': result[0],
        'f2': result[1]
    }
