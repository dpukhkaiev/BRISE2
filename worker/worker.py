import os
import sys
import subprocess
import logging
from random import choice

from worker_tools.rm_script import insert_config_to_RM_process, run_RM
from worker_tools.splitter import Splitter
from worker_tools.mock_values_corrector import correct_values


def energy_consumption(task_parameters: dict, scenario: dict):
    try:
        data = Splitter("scenarios/energy_consumption/" + scenario['ws_file'])
        data.search(str(task_parameters['frequency']), str(task_parameters['threads']))
        result = choice(data.new_data)
        return {
            'energy': float(result["EN"]),
            'time': float(result['TIM'])
        }
    except Exception as error:
        logging.getLogger(__name__).error("An error occurred during performing 'energy_consumption' Task with parameters %s: %s" % (task_parameters, error))


def naiveBayes_mock(task_parameters: dict, scenario: dict):
    try:
        data = Splitter("scenarios/rapid_miner/" + scenario['ws_file'])
        # Only for demo! 
        # To enable mock data to be used, real values of continuous parameters must be discretized
        corrected_bandwidth, corrected_min_bandwidth, corrected_num_kernels, corrected_app_grid_size = \
            correct_values(task_parameters['bandwidth'], task_parameters['minimum_bandwidth'], task_parameters['number_of_kernels'], task_parameters['application_grid_size'])
        data.searchNB(str(task_parameters['laplace_correction']), str(task_parameters['estimation_mode']),
                      str(task_parameters['bandwidth_selection']), str(corrected_bandwidth),
                      str(corrected_min_bandwidth), str(corrected_num_kernels),
                      str(task_parameters['use_application_grid']), str(corrected_app_grid_size))
        result = choice(data.new_data)
        
        return {
            'PREC_AT_99_REC': float(result["PREC_AT_99_REC"])
        }
    except Exception as error:
        logging.getLogger(__name__).error("An error occurred during performing 'taskNB' (NaiveBayes mock) Task with parameters %s: %s" % (task_parameters, error))
    return {
        'PREC_AT_99_REC':'NaN'
    }


def naiveBayes(task_parameters: dict, scenario: dict):    
    """Initialization function to run NaiveBayes algorithm inside RapidMiner

    :param task_parameters:dict: current measured configuration of NaiveBayes in a {key:value} format
    :param scenario:dict: parameters of scenario that is being processed

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

        RMprocess = insert_config_to_RM_process(algorithm, task_parameters, path2process)
    except Exception as error:
        logger.error("An error occurred during performing NaiveBayes Task with parameters %s: %s" % (task_parameters, error))
    return run_RM(path2RM, RMrepository, RMprocess, path2result)

def randomForest(task_parameters: dict, scenario: dict):
    """Initialization function to run RandomForest algorithm inside RapidMiner

    :param task_parameters:dict: current measured configuration of RandomForest in a {key:value} format
    :param scenario:dict: parameters of scenario that is being processed

    :rtype:float: average value of precision and recall
    """
    logger = logging.getLogger(__name__)
    # initialize all required pathes
    try:
        # use RapidMiner Automodel to define default config, if it is specified:
        automodel_default = True if "defined_by_automodel" in task_parameters.values() else False
        if automodel_default == True:
            algorithm = 'AUTO_MODEL'
            RMrepository = '//ServerRepository/Automodel/'
            path2process = '/home/w_user/.RapidMiner/repositories/ServerRepository/Automodel/Autommod.rmp'
        else:
            algorithm = 'RANDOM_FOREST'
            RMrepository = '//ServerRepository/RandomForest/'
            path2process = '/home/w_user/.RapidMiner/repositories/ServerRepository/RandomForest/MA_EXR_1_EX_2_RF_INV.rmp'
        path2result = './scenarios/rapid_miner/RF_performance.csv'
        path2RM = '/home/w_user/rapidminer-studio/scripts/rapidminer-batch.sh'

        RMprocess = insert_config_to_RM_process(algorithm, task_parameters, path2process)
    except Exception as error:
        logger.error("An error occurred during performing RandomForest Task with parameters %s: %s" % (task_parameters, error))
    return run_RM(path2RM, RMrepository, RMprocess, path2result)

def neuralNet(task_parameters: dict, scenario: dict):
    """Initialization function to run NeuralNet algorithm inside RapidMiner

    :param task_parameters:dict: current measured configuration of NeuralNet in a {key:value} format
    :param scenario:dict: parameters of scenario that is being processed

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
       
        RMprocess = insert_config_to_RM_process(algorithm, task_parameters, path2process)
    except Exception as error:
        logger.error("An error occurred during performing NeuralNet Task with parameters %s: %s" % (task_parameters, error))
    return run_RM(path2RM, RMrepository, RMprocess, path2result)



def SVM(task_parameters: dict, scenario: dict):
    """Initialization function to run Support Vector Machine (SVM) algorithm inside RapidMiner

    :param task_parameters:dict: current measured configuration of Support Vector Machine (SVM) in a {key:value} format
    :param scenario:dict: parameters of scenario that is being processed

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

        RMprocess = insert_config_to_RM_process(algorithm, task_parameters, path2process)
    except Exception as error:
        logger.error("An error occurred during performing SVM Task with parameters %s: %s" % (task_parameters, error))
    return run_RM(path2RM, RMrepository, RMprocess, path2result)

def genetic(task_parameters: dict, scenario: dict):
    logger = logging.getLogger(__name__)
    try:
        generations = str(task_parameters['generations'])
        populationSize = str(task_parameters['populationSize'])
        numTopLevelComponents = str(scenario['numTopLevelComponents'])
        avgNumImplSubComponents = str(scenario['avgNumImplSubComponents'])
        implSubComponentStdDerivation = str(scenario['implSubComponentStdDerivation'])
        avgNumCompSubComponents = str(scenario['avgNumCompSubComponents'])
        compSubComponentStdDerivation = str(scenario['compSubComponentStdDerivation'])
        componentDepth = str(scenario['componentDepth'])
        numImplementations = str(scenario['numImplementations'])
        excessComputeResourceRatio = str(scenario['excessComputeResourceRatio'])
        numRequests = str(scenario['numRequests'])
        numCpus = str(scenario['numCpus'])
        seed = str(scenario['seed'])
        timeoutValue = str(scenario['timeoutValue'])
        timeoutUnit = str(scenario['timeoutUnit'])
        ##
        treeMutateOperatorP = str(task_parameters['treeMutateOperatorP'])
        treeMutateOperatorP1 = str(task_parameters['treeMutateOperatorP1'])
        treeMutateOperatorP2 = str(task_parameters['treeMutateOperatorP2'])
        treeMutateOperatorP3 = str(task_parameters['treeMutateOperatorP3'])
        ##
        ###
        Lambda = str(task_parameters['lambda'])
        crossoverRate = str(task_parameters['crossoverRate'])
        mu = str(task_parameters['mu'])
        tournament = str(task_parameters['tournament'])
        ###

        ws_file ="result_v{}_q{}_d{}_r{}.csv".\
            format(numImplementations, numRequests, componentDepth, excessComputeResourceRatio)

        file_name = "results/scenarios/"+ws_file

        command = ("java -jar binaries/jastadd-mquat-solver-genetic-2.0.0-SNAPSHOT.jar %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s"
                          % (numTopLevelComponents, avgNumImplSubComponents, implSubComponentStdDerivation, avgNumCompSubComponents,
                             compSubComponentStdDerivation, componentDepth, numImplementations, excessComputeResourceRatio, numRequests,
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
        logger.error("An error occurred during performing 'genetic' Task with parameters %s: %s" % (task_parameters, error))
    return {
        'Validity':'NaN'
    }

def simulatedAnnealing(param, scenario):
    logger = logging.getLogger(__name__)
    try:
        # params
        subComponentUnassignedFactor = str(param['subComponentUnassignedFactor'])
        softwareComponentUnassignedFactor = str(param['softwareComponentUnassignedFactor'])
        hardScoreStartingTemperaturePercentage = str(param['hardScoreStartingTemperaturePercentage'])
        softScoreStartingTemperaturePercentage = str(param['softScoreStartingTemperaturePercentage'])
        acceptedCountLimit = str(param['acceptedCountLimit'])
        millisecondsSpentLimit = str(param['millisecondsSpentLimit'])
        unimprovedMillisecondsSpentLimit = str(param['unimprovedMillisecondsSpentLimit'])

        # scenario

        ws_file = str(scenario['ws_file'])
        numTopLevelComponents = str(scenario['numTopLevelComponents'])
        avgNumImplSubComponents = str(scenario['avgNumImplSubComponents'])
        implSubComponentStdDerivation = str(scenario['implSubComponentStdDerivation'])
        avgNumCompSubComponents = str(scenario['avgNumCompSubComponents'])
        compSubComponentStdDerivation = str(scenario['compSubComponentStdDerivation'])
        componentDepth = str(scenario['componentDepth'])
        numImplementations = str(scenario['numImplementations'])
        excessComputeResourceRatio = str(scenario['excessComputeResourceRatio'])
        numRequests = str(scenario['numRequests'])
        numCpus = str(scenario['numCpus'])
        seed = str(scenario['seed'])
        # file_name = "result_v{}_q{}_d{}_r{}.csv".\
        #     format(numImplementations, numRequests, componentDepth, excessComputeResourceRatio.replace('.', '_'))
        import os
        command = ("java -jar binaries/jastadd-mquat-solver-mh-1.0-SNAPSHOT.jar %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s"
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
    except Exception as e:
        logger.error("ERROR IN WORKER during performing SA with parameters: %s" % param)
    return {
        'hardScoreImprovement': 'NaN',
        'softScoreImprovement': 'NaN'
    }
