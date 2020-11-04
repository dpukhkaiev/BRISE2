__doc__ = """
    Module to load configurations and experiment descriptions."""
import logging
from typing import Dict

from core_entities.search_space import Hyperparameter, initialize_search_space
from tools.file_system_io import load_json_file
from tools.front_API import API
from tools.json_validator import (
    get_duplicated_sc_names,
    get_missing_sc_entities,
    is_json_file_valid
)


def load_experiment_setup(exp_desc_file_path: str) -> [Dict, Hyperparameter]:
    """
    Method reads the Experiment Description from specified file and performs it validation according to specified
        schema. It also loads a search space for the specified experiment from correspondent data file
    :param exp_desc_file_path: String. Relative path to Experiment Description file from root of main node folder.
    :return: loaded Experiment Description, loaded search space
    """
    # Load Experiment description from json file.
    task_description = load_json_file(exp_desc_file_path)
    framework_settings = load_json_file('./Resources/SettingsBRISE.json')

    # TODO: add versions of experiment description for compatibility checks
    experiment_description = {**task_description, **framework_settings}
    # Validate and load Search space
    search_space_description = load_json_file(experiment_description["DomainDescription"]["DataFile"])
    # TODO: fix validation
    validate_experiment_data(search_space_description)
    search_space = initialize_search_space(search_space_description, experiment_description["SelectionAlgorithm"])
    logging.getLogger(__name__).info(
        f"The Experiment Description was loaded from {exp_desc_file_path}. "
        f"Search space was loaded from {experiment_description['DomainDescription']['DataFile']}."
    )

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
    validity_check = is_json_file_valid(validated_data=experiment_description, schema_path=schema_file_path)
    uniqueness_check = get_duplicated_sc_names(experiment_description)
    presence_check = get_missing_sc_entities(experiment_description)
    if not validity_check:
        msg = f"Provided Experiment Description has not passed the validation using schema in file {schema_file_path}."
        logger.error(msg)
        API().send('log', 'error', message=msg)
    if uniqueness_check:
        msg = f"Some Stop Condition instances are duplicated: {uniqueness_check}."
        logger.error(msg)
        API().send('log', 'error', message=msg)
    if presence_check:
        msg = f"Some Stop Conditions defined in Stop Condition Trigger Logic expression are missing: {presence_check}."
        logger.error(msg)
        API().send('log', 'error', message=msg)

    if validity_check and not uniqueness_check and not presence_check:
        logger.info("Provided Experiment Description is valid.")
    else:
        msg = "Some errors caused during validation. Please, check the Experiment Description."
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
