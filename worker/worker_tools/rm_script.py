import os
import csv
import xml.etree.ElementTree as ET
import time
import subprocess
import logging

def insert_config_to_RM_process(algorithm :str, task_parameters :dict, path2process :str):

    """ Gets configuration to be measured in RapidMiner and inserts it into RM process

    :param algorithm:str: name of the algorithm to be run (currently supported values: 'NAIVE_BAYES', 'RANDOM_FOREST', 'AUTO_MODEL', 'NEURAL_NET', 'SUPPORT_VECTOR_MACHINE')
    :param task_parameters:dict: configuration to be measured
    :param path2process:str: path to the RM process (rmp file)

    :rtype:str: name of the modified RM process
    """
    logger = logging.getLogger(__name__)
    logger.info("******* Measurement for the algorithm %s ***********" % algorithm)
    logger.info("Start measurements with configuration:\n %s" % task_parameters)
    try:
        tree = ET.parse(path2process)  
        root = tree.getroot()

        for elem in root.iter('operator'):  
            if elem.attrib['name'] == algorithm:
                for subelem in elem.iter('parameter'):
                    for task_parameter in task_parameters:
                        if task_parameter == subelem.get('key'):
                            subelem.set('value', task_parameters[task_parameter])

        tree.write(path2process)
        return path2process.rsplit('/', 1)[-1]
    except FileNotFoundError:
        logger.error("rmp file with process doesn\'t exist in %s" % path2process)


def run_RM(path2RM :str, RMrepository :str, RMprocess :str, path2result :str):    
    """ Run process with RapidMiner

    :param path2RM:str: path to the RapidMiner-Studio (rapidminer-batch.sh file)
    :param RMrepository:str: RMrepository - name of the RM repository used
    :param RMprocess:str: RM process to run
    :param path2result:str: path to the file with final results

    :rtype:float: average value of precision and recall
    """
    logger = logging.getLogger(__name__)
    prec = ""
    rec = ""
    result = None
    try:
        # prepare results file, that is going to be used by RapidMiner to insert the result
        with open(path2result, "w+") as result_file:
            if RMprocess is not None:
                begin_time = time.time()
                cmd = 'sh ' + path2RM + ' "' + RMrepository + RMprocess.strip('.rmp') + '"'
                subprocess.check_call(cmd, shell=True)  
                end_time = time.time()
                exec_time = end_time - begin_time
                logger.info("Execution time: %s sec" % str(exec_time))
            else:
                raise ChildProcessError("RapidMiner process run was not successful!")

        # get result from resulting file
        with open(path2result, 'r') as result_file:
            reader = csv.reader(result_file)        
            for row in reader:
                if row != []:
                    prec = row[len(row) - 3]
                    rec = row[len(row) - 2]
                else:
                    logger.debug("Row is empty!")
        try:
            result = float(prec)*0.5 + float(rec)*0.5
            logger.info("Final result: %f with precision: %f and recall: %f" % (result, prec, rec))
        except ValueError:
            logger.warning("Non-float result was received from RapidMiner!")
    except Exception as error:
        logger.error("ERROR occured while getting results from RapidMiner: %s" % error)
    return {
        'prec_rec': result
    }
