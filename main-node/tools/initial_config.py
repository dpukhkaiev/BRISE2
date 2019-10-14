__doc__ = """
    Module to load configurations and experiment descriptions."""
import logging
from sys import argv

from tools.file_system_io import load_json_file, create_folder_if_not_exists
from tools.json_validator import is_json_file_valid
from tools.front_API import API


def load_global_config(global_config_path: str = './GlobalConfig.json'):
    """
    Method reads configuration for BRISE from GlobalConfig.json configuration file.
    :param global_config_path: sting path to file.
    :return: dict with configuration for BRISE
    """
    logger = logging.getLogger(__name__)

    # Check if main.py running with a specified global configuration file path
    if len(argv) > 2:
        global_config_path = argv[2]

    config = load_json_file(global_config_path)
    create_folder_if_not_exists(config['results_storage'])
    logger.info("Global BRISE configuration loaded from file '%s'" % global_config_path)
    return config


def load_experiment_description(exp_desc_file_path: str = './Resources/EnergyExperiment.json'):
    """
    Method reads the Experiment Description from specified file and performs it validation according to specified
        schema.
    :param exp_desc_file_path: String. Relative path to Experiment Description file from root of main node folder.
    :return: Dictionary. Loaded Experiment Description.
    """
    # Check if main.py running with a specified experiment description file path
    if len(argv) > 1:
        exp_desc_file_path = argv[1]

    # Load Experiment description from json file.
    experiment_description = load_json_file(exp_desc_file_path)

    # Add Parameters data to experiment description
    data = load_json_file(experiment_description["DomainDescription"]["DataFile"])
    experiment_data_configurations = []
    # TODO the dimensions validation in the task data file
    for dimension in experiment_description["DomainDescription"]["ParameterNames"]:
        experiment_data_configurations.append(data[dimension])
    experiment_description["DomainDescription"]["AllConfigurations"] = experiment_data_configurations

    # Validate Experiment description file.
    logging.getLogger(__name__).info("The Experiment Description was loaded from the file '%s'." % exp_desc_file_path)

    return experiment_description


def validate_experiment_description(experiment_description: dict,
                                    schema_file_path: str = './Resources/schema/experiment.schema.json'):
    """
    Performs validation and raises error if provided Experiment Description does not pass the validation
        according to the schema
    :param experiment_description: Dict. Experiment Description.
    :param schema_file_path:
    :return:
    """
    logger = logging.getLogger(__name__)

    if is_json_file_valid(experiment_description=experiment_description, schema_path=schema_file_path):
        logger.info("Provided Experiment Description is valid.")
    else:
        msg = "Provided Experiment Description have not passed the validation using schema in file %s. " \
              "Experiment description: \n%s" % (schema_file_path, experiment_description)
        logger.error(msg)
        API().send('log', 'error', message=msg)
        raise ValueError(msg)


if __name__ == "__main__":
    logging.warn("Loaded Global config:\n%s" % load_global_config())
    logging.warn("Loaded Experiment description:\n%s" % load_experiment_description())
