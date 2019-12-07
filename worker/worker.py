import os
import sys
import subprocess
import logging
from random import choice
import time

from worker_tools.splitter import Splitter


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
        logging.getLogger(__name__).error(
            "An error occurred during performing 'energy_consumption' Task with parameters %s: %s" % (
                task_parameters, error))

def spark(task_parameters: dict, scenario: dict):
    """
    This is a worker method for the HDP Spark use case. It runs a 'spark-submit' command on Spark node
    via SSH with parameters specified in 'task_parameters'
    :param task_parameters: dict. Configuration to be measured (values for the 'spark-submit' command parameters)
    :param scenario: dict. static experiments'/tasks' configurations (if any) that need to be passed to Worker (not applicable for the Spark use case)
    :return: dict. Time taken to run 'spark-submit' command on the remote node via SSH 
    """
    master = str(task_parameters['master'])
    deploy_mode = str(task_parameters['deploy_mode'])
    driver_memory = str(task_parameters['driver_memory'])
    num_executors = str(task_parameters['num_executors'])
    executor_memory = str(task_parameters['executor_memory'])
    executor_cores = str(task_parameters['executor_cores'])
    spark_python_worker_reuse = str(task_parameters['spark.python.worker.reuse'])
    spark_reducer_maxSizeInFlight = str(task_parameters['spark.reducer.maxSizeInFlight'])
    spark_shuffle_compress = str(task_parameters['spark.shuffle.compress'])
    spark_shuffle_file_buffer = str(task_parameters['spark.shuffle.file.buffer'])
    spark_broadcast_compress = str(task_parameters['spark.broadcast.compress'])
    spark_memory_fraction = str(task_parameters['spark.memory.fraction'])
    spark_memory_storageFraction = str(task_parameters['spark.memory.storageFraction'])
    spark_dynamicAllocation_enabled = str(task_parameters['spark.dynamicAllocation.enabled'])
    spark_shuffle_service_enabled = str(task_parameters['spark.shuffle.service.enabled'])

    command = "ssh-keyscan -H spark_service >> /root/.ssh/known_hosts"
    
    # dependent parameters have value 'None' if their parent parameter's value is not enabling. However 'None' shouldn't be passed as a 
    # parameter for the 'spark-submit' command. That's why if dependent parameter has None value it shouldn't be mentioned at all in command
    dynamicAllocation_dependent = " "
    
    if spark_dynamicAllocation_enabled != "None":
        dynamicAllocation_dependent = " --conf spark.dynamicAllocation.enabled=" + spark_dynamicAllocation_enabled

    command = "ssh -o 'StrictHostKeyChecking no' -i /root/.ssh/id_rsa root@spark_service '/usr/lib/spark/1.3.1/bin/spark-submit"\
        " --master " + master + \
        " --deploy-mode " + deploy_mode + \
        " --driver-memory " + driver_memory + "g" + \
        " --num-executors " + num_executors + \
        " --executor-memory " + executor_memory + "g" + \
        " --executor-cores " + executor_cores + \
        " --conf spark.python.worker.reuse=" + spark_python_worker_reuse + \
        " --conf spark.reducer.maxSizeInFlight=" + spark_reducer_maxSizeInFlight + "m" + \
        " --conf spark.shuffle.compress=" + spark_shuffle_compress + \
        " --conf spark.shuffle.file.buffer=" + spark_shuffle_file_buffer + "k" + \
        " --conf spark.broadcast.compress=" + spark_broadcast_compress + \
        " --conf spark.memory.fraction=" + spark_memory_fraction + \
        " --conf spark.memory.storageFraction=" + spark_memory_storageFraction + \
        dynamicAllocation_dependent + \
        " --conf spark.shuffle.service.enabled=" + spark_shuffle_service_enabled + \
        " /usr/src/app/workload.py'"
    start = time.time()
    try:
        result = subprocess.check_call(command, shell=True)
    except Exception as error:
       logging.getLogger(__name__).error("Spark process failed with parameters %s : %s" % (task_parameters, error))
       return {
           'time': 'NaN'
       }
    finish = time.time()
    res = float(finish) - float(start)
    return {
        'time': float(res)
    }

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

        ws_file = "result_v{}_q{}_d{}_r{}.csv". \
            format(numImplementations, numRequests, componentDepth, excessComputeResourceRatio)

        file_name = "results/scenarios/" + ws_file

        command = (
                "java -jar binaries/jastadd-mquat-solver-genetic-2.0.0-SNAPSHOT.jar %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s"
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
        logger.error("An error occurred during performing 'genetic' Task with parameters %s: %s" % (task_parameters, error))
    return {
        'Validity':'NaN'
    }
