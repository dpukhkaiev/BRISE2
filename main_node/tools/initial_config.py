__doc__ = """
    Module to load configurations and experiment descriptions."""

import logging
import os
from typing import Dict, Tuple

from core_entities.search_space import SearchSpace
from tools.file_system_io import load_json_file


def load_experiment_setup(exp_desc_file_path: str) -> Tuple[Dict, SearchSpace]:
    """
    Method reads the Experiment Description from a specified file.
    :param exp_desc_file_path: String. Relative path to Experiment Description file from root of main node folder.
    :return: loaded Experiment Description, loaded search space
    """
    # Load Experiment description from json file.
    experiment_description = load_json_file(exp_desc_file_path)
    search_space_description = experiment_description["Context"]["SearchSpace"]
    search_space = SearchSpace(search_space_description)

    # Automatically add BenchmarkIdentifier based on the test case filename
    # This ensures that experiments from the same test case (but different repetitions) are grouped together
    if "BenchmarkIdentifier" not in experiment_description.get("Context", {}):
        # Extract filename without extension to use as identifier
        # e.g., "test_case_0.json" -> "test_case_0"
        filename = os.path.basename(exp_desc_file_path)
        benchmark_id = os.path.splitext(filename)[0]

        experiment_description["Context"]["BenchmarkIdentifier"] = benchmark_id
        logging.getLogger(__name__).info(f"Automatically added BenchmarkIdentifier '{benchmark_id}' based on filename.")

    logging.getLogger(__name__).info(f"The Experiment Description was loaded from {exp_desc_file_path}. ")
    return experiment_description, search_space
