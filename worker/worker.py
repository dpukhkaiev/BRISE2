import os
import sys
import subprocess
import logging
from random import randint, choice

from csv_data.splitter import Splitter


def energy_consumption(task_parameters: dict, scenario: dict):
    try:
        data = Splitter("csv_data/"+scenario['ws_file'])
        data.search(str(task_parameters['frequency']), str(task_parameters['threads']))
        result = choice(data.new_data)
        return {
            'energy': float(result["EN"])
        }
    except Exception as error:
        logging.getLogger(__name__).error("An error occurred during performing 'energy_consumption' Task with parameters %s: %s" % (task_parameters, error))


def taskNB(task_parameters: dict, scenario: dict):
    try:
        data = Splitter("csv_data/"+scenario['ws_file'])
        data.searchNB(str(task_parameters['laplace_correction']), str(task_parameters['estimation_mode']),
                      str(task_parameters['bandwidth_selection']), str(task_parameters['bandwidth']),
                      str(task_parameters['minimum_bandwidth']), str(task_parameters['number_of_kernels']),
                      str(task_parameters['use_application_grid']), str(task_parameters['application_grid_size']))
        result = choice(data.new_data)
        return {
            'PREC_AT_99_REC': float(result["PREC_AT_99_REC"])
        }
    except Exception as error:
        logging.getLogger(__name__).error("An error occurred during performing 'taskNB' Task with parameters %s: %s" % (task_parameters, error))


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
        logging.getLogger(__name__).error("An error occurred during performing 'genetic' Task with parameters %s: %s" % (task_parameters, error))
