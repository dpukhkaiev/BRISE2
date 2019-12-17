__doc__ = """
    Module to generate a skeleton of code from Experiment Description."""
import os
import json
import logging
from jinja2 import Environment, FileSystemLoader


def generate_worker_function(experiment_description_path):
    """
        The method takes a path to an experiment description and appends scenario skeleton to worker/worker.py
        :experiment_description_path : sting path to a experiment description json file.
        """
    logger = logging.getLogger(__name__)
    try:
        file_loader = FileSystemLoader(os.path.dirname(__file__) + '/templates')
        env = Environment(loader=file_loader)
        template = env.get_template('worker_f_template')
    except IOError as error:
        logger.error("Error with reading %s/templates/worker_f_template file: %s" % (os.path.dirname(__file__), error))
        raise error
    # TODO: Usage of shared functionality - load_json_file
    try:
        with open(experiment_description_path) as json_file:
            data = json.load(json_file)
    except IOError as error:
        logger.error("Error with reading %s file: %s" % (experiment_description_path, error))
        raise error
    except json.JSONDecodeError as error:
        logger.error("Error with decoding %s json file: %s" % (experiment_description_path, error))
        raise error
    in_parameters = data['TaskConfiguration']['TaskParameters']
    in_scenario = data['TaskConfiguration']['Scenario'].keys()
    out_parameters = data['TaskConfiguration']['ResultStructure']
    task_name = data['TaskConfiguration']['TaskName']
    output = template.render(in_parameters=in_parameters, in_scenario=in_scenario, out_parameters=out_parameters, task_name=task_name)
    with open("./worker/worker.py", "r") as f:
        file = f.read()
        f.close()
    if output.partition('\n')[0] not in file:
        with open("./worker/worker.py", "a+") as f:
            f.write(output)
            f.close()
            logger.info("The new method has been added to the worker.")
    else:
        logger.info("The method with the same name already exists.")