__doc__ = """
    Module to load configurations and experiment descriptions."""
import logging
from typing import Dict

from core_entities.search_space import SearchSpace
from tools.file_system_io import load_json_file


def load_experiment_setup(exp_desc_file_path: str) -> [Dict, SearchSpace]:
    """
    Method reads the Experiment Description from a specified file.
    :param exp_desc_file_path: String. Relative path to Experiment Description file from root of main node folder.
    :return: loaded Experiment Description, loaded search space
    """
    # Load Experiment description from json file.
    experiment_description = load_json_file(exp_desc_file_path)
    search_space_description = experiment_description["Context"]["SearchSpace"]
    search_space = SearchSpace(search_space_description)
    logging.getLogger(__name__).info(
        f"The Experiment Description was loaded from {exp_desc_file_path}. "
    )
    return experiment_description, search_space
