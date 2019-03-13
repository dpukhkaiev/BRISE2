__doc__ = """
    Module to read config and tasks for execute."""
import json
import logging

from tools.file_system_io import load_json_file, create_folder_if_not_exists
from tools.json_validator import is_experiment_description_valid


def read_global_config(global_config_path):
    """
    Method reads configuration for BRISE from GlobalConfig.json configuration file.
    :param global_config_path: sting path to file.
    :return: dict with configuration for BRISE
    """
    logger = logging.getLogger(__name__)
    try:
        config = load_json_file(global_config_path)
        return config

    except IOError as e:
        logger.error('No config file found: %s' % e, exc_info=True)
        exit(3)
    except ValueError as e:
        logger.error('Invalid configuration file: %s' % e, exc_info=True)
        exit(3)


def load_experiment_description(path_to_file):
    """
    Method reads task configuration from task.json file.
    :param path_to_file: sting path to task file.
    :return: dict with task parameters and task data.
    """
    # TODO: Add task file validation. The file contains all parameters of the task that BRISE require
    logger = logging.getLogger(__name__)
    try:
        experiment_description = load_json_file(path_to_file)
        data = load_json_file(experiment_description["DomainDescription"]["DataFile"])
        all_configurations = []
        # TODO the dimensions validation in the task data file
        for dimension in experiment_description["DomainDescription"]["FeatureNames"]:
            all_configurations.append(data[dimension])
        experiment_description["DomainDescription"]["AllConfigurations"] = all_configurations
    except IOError as e:
        logger.error('Error with reading task.json file: %s' % e, exc_info=True)
        exit(1)
    except json.JSONDecodeError as e:
        logger.error('Error with decoding task: %s' % e, exc_info=True)
        exit(1)
    return experiment_description


def initialize_config(argv):
    """
    Load global config and task config.
    :return: (dict globalConfiguration, dict taskConfiguration)
    """
    logger = logging.getLogger(__name__)

    experiment_description_path = argv[1] if len(argv) > 1 else './Resources/EnergyExperiment.json'
    global_config_path = argv[2] if len(argv) > 2 else './GlobalConfig.json'
    experiment_schema_path = './Resources/schema/experiment.schema.json'  # validation for experiment.json in `taskPath`

    logger.info("Global BRISE configuration file: %s, task description file path: %s"
                % (experiment_description_path, global_config_path))
    #   Reading config file
    globalConfig = read_global_config(global_config_path)

    #   Loading task config and creating config points distribution according to Sobol.
    # {"task_name": String, "params": Dict, "taskDataPoints": List of points }
    experiment_description = load_experiment_description(experiment_description_path)

    create_folder_if_not_exists(globalConfig['results_storage'])

    if is_experiment_description_valid(schema_path=experiment_schema_path, file_path=experiment_description_path):
        logger.info("Experiment file %s is valid." % experiment_description_path)
        return globalConfig, experiment_description
    else:
        logger.error("Experiment file %s have not passed the validation." % experiment_description_path)
        exit(1)


if __name__ == "__main__":
    initialize_config({})
