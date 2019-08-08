__doc__ = """
    Module to read config and tasks for execute."""
import json
import logging
import zlib

from tools.file_system_io import load_json_file, create_folder_if_not_exists
from tools.front_API import API
from tools.json_validator import is_json_file_valid


def read_global_config(global_config_path):
    """
    Method reads configuration for BRISE from GlobalConfig.json configuration file.
    :param global_config_path: sting path to file.
    :return: dict with configuration for BRISE
    """
    logger = logging.getLogger(__name__)
    sub = API()
    try:
        config = load_json_file(global_config_path)
        return config

    except IOError as error:
        logger.error('No config file found: %s' % error, exc_info=True)
        sub.send('log', 'error', message='No config file found: %s' % error)
        raise error
    except ValueError as error:
        logger.error('Invalid configuration file: %s' % error, exc_info=True)
        sub.send('log', 'error', message='Invalid configuration file: %s' % error)
        raise error


def load_experiment_description(path_to_file):
    """
    Method reads experiment description from ExperimentDescription.json file.
    :param path_to_file: sting path to task file.
    :return: dict with task parameters and task data.
    """
    # TODO: Add task file validation. The file contains all parameters of the task that BRISE require
    logger = logging.getLogger(__name__)
    sub = API()
    try:
        experiment_description = load_json_file(path_to_file)
        data = load_json_file(experiment_description["DomainDescription"]["DataFile"])
        experiment_data_configurations = []
        # TODO the dimensions validation in the task data file
        for dimension in experiment_description["DomainDescription"]["FeatureNames"]:
            experiment_data_configurations.append(data[dimension])
        experiment_description["DomainDescription"]["AllConfigurations"] = experiment_data_configurations
    except IOError as error:
        logger.error('Error with reading ExperimentDescription.json file: %s' % error, exc_info=True)
        sub.send('log', 'error', message='Error with reading task.json file: %s' % error)
        raise error
    except json.JSONDecodeError as error:
        logger.error('Error with decoding experiment description: %s' % error, exc_info=True)
        sub.send('log', 'error', message='Error with decoding task: %s' % error)
        raise error
    return experiment_description


def initialize_config(argv):
    """
    Load global config and task config.
    :return: (dict globalConfiguration, dict taskConfiguration)
    """
    logger = logging.getLogger(__name__)
    sub = API()

    experiment_description_path = argv[1] if len(argv) > 1 else './Resources/EnergyExperiment.json'
    global_config_path = argv[2] if len(argv) > 2 else './GlobalConfig.json'
    experiment_schema_path = './Resources/schema/experiment.schema.json'  # validation for experiment.json in `taskPath`

    logger.info("Global BRISE configuration file: %s, task description file path: %s"
                % (experiment_description_path, global_config_path))
    #   Reading global config file
    global_config = read_global_config(global_config_path)

    #   Loading experiment description file
    experiment_description = load_experiment_description(experiment_description_path)

    create_folder_if_not_exists(global_config['results_storage'])

    if is_json_file_valid(schema_path=experiment_schema_path, file_path=experiment_description_path):
        logger.info("Experiment description file %s is valid." % experiment_description_path)
        return global_config, experiment_description
    else:
        logger.error("Experiment description file %s have not passed the validation." % experiment_description_path)
        sub.send('log', 'error', message="Experiment description file %s is NOT valid" % experiment_description_path)
        raise ValueError("Experiment description file %s is NOT valid" % experiment_description_path)


if __name__ == "__main__":
    initialize_config({})
