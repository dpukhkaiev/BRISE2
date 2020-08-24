__doc__ = """
    Module to load configurations and experiment descriptions."""
import logging
from typing import Tuple

from tools.file_system_io import load_json_file, create_folder_if_not_exists
from tools.json_validator import is_json_file_valid
from tools.front_API import API
from core_entities.search_space import from_json, Hyperparameter


def load_experiment_setup(exp_desc_file_path: str) -> Tuple[dict, Hyperparameter]:
    """
    Method reads the Experiment Description from specified file and performs it validation according to specified
        schema. It also loads a search space for the specified experiment from correspondent data file
    :param exp_desc_file_path: String. Relative path to Experiment Description file from root of main node folder.
    :return: loaded Experiment Description, loaded search space
    """
    # Load Experiment description from json file.
    task_description = load_json_file(exp_desc_file_path)
    framework_settings = load_json_file('./Resources/SettingsBRISE.json')

    experiment_description = {**task_description, **framework_settings}
    # Validate and load Search space
    search_space_to_validate = load_json_file(experiment_description["DomainDescription"]["DataFile"])
    # validate_experiment_data(search_space_to_validate) TODO update schema after stabilizing data file structure

    search_space = from_json(experiment_description["DomainDescription"]["DataFile"])
    #create_folder_if_not_exists(experiment_description["General"]["results_storage"])
    logging.getLogger(__name__).info("The Experiment Description was loaded from the file '%s'. Search space was loaded from the file '%s'." \
        % (exp_desc_file_path, experiment_description["DomainDescription"]["DataFile"]))

    return experiment_description, search_space


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

    if is_json_file_valid(validated_data=experiment_description, schema_path=schema_file_path):
        logger.info("Provided Experiment Description is valid.")
    else:
        msg = "Provided Experiment Description have not passed the validation using schema in file %s. " \
              "Experiment description: \n%s" % (schema_file_path, experiment_description)
        logger.error(msg)
        API().send('log', 'error', message=msg)
        raise ValueError(msg)

def validate_experiment_data(experiment_data: dict,
                                    schema_file_path: str = './Resources/schema/experiment_data.schema.json'):
    """
    Performs validation and raises error if provided Experiment Data does not pass the validation
        according to the schema
    :param experiment_data: Dict. Experiment Data.
    :param schema_file_path:
    :return:
    """
    logger = logging.getLogger(__name__)

    if is_json_file_valid(validated_data=experiment_data, schema_path=schema_file_path):
        logger.info("Provided Experiment Data is valid.")
    else:
        msg = "Provided Experiment Data has not passed the validation using schema in file %s. " \
              "Experiment data: \n%s" % (schema_file_path, experiment_data)
        logger.error(msg)
        API().send('log', 'error', message=msg)
        raise ValueError(msg)
