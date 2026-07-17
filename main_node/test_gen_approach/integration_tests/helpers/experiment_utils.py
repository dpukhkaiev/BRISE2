import json
import math
from traceback import print_stack
from pathlib import Path
from typing import List

from default_config_handler.default_configuration_handler_orchestrator import (
    DefaultConfigHandlerOrchestrator,
)
from tools.reflective_class_import import reflective_class_import

from core_entities.configuration import Configuration

from core_entities.search_space import get_search_space_record

from core_entities.search_space import SearchSpace

from core_entities.experiment import Experiment

from configuration_selection.configuration_selection import ConfigurationSelection
from tools.initial_config import load_experiment_setup

PHASE1_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "test_generation" / "output_configs"


def load_phase1_config(config_filename: str):
    """Load a Phase 1 output config by filename.

    Returns (experiment_description, search_space) — same as load_experiment_setup.
    Path is relative to main_node/ (where pytest is run from).
    """
    path = PHASE1_OUTPUT_DIR / config_filename
    with open(path) as f:
        exp_desc = json.load(f)
    search_space = SearchSpace(exp_desc["Context"]["SearchSpace"])
    return exp_desc, search_space


def create_experiment_from_test_case(test_case_number: int, get_experiment_fixture):
    try:
        experiment_description, search_space = get_experiment_fixture(test_case_number)
        if experiment_description is None or search_space is None:
            return None, None, None

        experiment = Experiment(experiment_description, search_space)
        return experiment, experiment_description, search_space

    except Exception as e:
        print(f"Failed to create experiment from test case {test_case_number}: {e}")
        print_stack()
        return None, None, None


def get_objective_count(experiment: Experiment):
    try:
        objectives = experiment.description["Context"]["TaskConfiguration"][
            "Objectives"
        ]
        return len(objectives.keys())
    except (KeyError, TypeError, AttributeError):
        return None


def get_parameter_types(experiment: Experiment):
    try:
        search_space_str = json.dumps(experiment.description["Context"]["SearchSpace"])

        if "OrdinaryHyperparameter" in search_space_str:
            return "all_types"
        elif "NominalHyperparameter" in search_space_str:
            return "float_nom"
        elif "FloatHyperparameter" in search_space_str:
            return "2_float"
        else:
            return None
    except (KeyError, TypeError, AttributeError):
        return None


def has_default_config_handler(experiment: Experiment):
    try:
        return "DefaultConfigurationHandler" in experiment.description.keys()
    except (AttributeError, TypeError):
        return False


def has_transfer_learning(experiment: Experiment):
    try:
        return "TransferLearning" in experiment.description.keys()
    except (AttributeError, TypeError):
        return False


def write_experiment_to_db(experiment: Experiment, search_space: SearchSpace):
    try:
        experiment.database.write_one_record(
            "Experiment_description", experiment.get_experiment_description_record()
        )
        experiment.database.write_one_record(
            "Search_space", get_search_space_record(search_space, experiment.unique_id)
        )
        return True
    except Exception as e:
        print(f"Failed to write experiment to database: {e}")
        print_stack()
        return False


def setup_task_configuration(experiment: Experiment):
    try:
        Configuration.set_task_config(
            experiment.description["Context"]["TaskConfiguration"]
        )
        return True
    except (KeyError, TypeError, AttributeError) as e:
        print(f"Failed to setup task configuration: {e}")
        return False


def get_configuration_fixture_name(parameter_types: str):
    return f"get_configurations_{parameter_types}"


def create_configuration_selection(experiment: Experiment):
    try:
        return ConfigurationSelection(experiment)
    except Exception as e:
        print(f"Failed to create ConfigurationSelection: {e}")
        print_stack()
        return None


def get_surrogate_type_from_description(experiment: Experiment):
    try:
        predictor_config = experiment.description.get("ConfigurationSelection", {}).get(
            "Predictor", {}
        )

        if "Model" in predictor_config:
            surrogate_instance = (
                predictor_config["Model"].get("Surrogate", {}).get("Instance", {})
            )
            if surrogate_instance:
                return list(surrogate_instance.keys())[0]

        if "Model_0" in predictor_config:
            surrogate_instance = (
                predictor_config["Model_0"].get("Surrogate", {}).get("Instance", {})
            )
            if surrogate_instance:
                return list(surrogate_instance.keys())[0]

        # Fallback ->search for any "Model_N" key
        for key in predictor_config.keys():
            if key.startswith("Model"):
                surrogate_instance = (
                    predictor_config[key].get("Surrogate", {}).get("Instance", {})
                )
                if surrogate_instance:
                    return list(surrogate_instance.keys())[0]

        return None

    except (KeyError, TypeError, AttributeError, IndexError):
        return None


def get_min_samples_for_tl(experiment: Experiment):
    try:
        if not has_transfer_learning(experiment):
            return None

        min_samples = experiment.description["TransferLearning"][
            "TransferExpediencyDetermination"
        ]["SamplingLandmarkBased"]["MinNumberOfSamples"]
        return min_samples - 1
    except (KeyError, TypeError, AttributeError):
        return None


def get_default_configuration(experiment: Experiment):
    try:
        dch_o = DefaultConfigHandlerOrchestrator()
        default_config_handler = dch_o.get_default_configuration_handler(
            experiment=experiment
        )
        return default_config_handler.get_default_configuration()
    except Exception as e:
        print(f"Failed to get default configuration: {e}")
        print_stack()
        return None


def instantiate_all_scs(experiment: Experiment) -> List:
    """Instantiate every SC instance defined in the experiment description.

    Unlike launch_stop_condition_threads, this bypasses the Expression filter
    so it works for Phase 1 configs where SC Names (SC1–SC7) do not appear as
    substrings in the Expression ("StopCondition1").

    AdaptiveType is skipped when the search space is infinite (all
    FloatHyperparameter-only search spaces have size np.inf, which AdaptiveType
    rejects by calling publish() and never setting self.max_configs).

    Any other SC that fails to instantiate is also silently skipped.

    Returns: list of successfully instantiated SC objects.
    """
    scs = []
    try:
        sc_desc = experiment.description.get("StopCondition", {})

        # Check search-space size once — needed to guard AdaptiveType.
        ss_record = experiment.database.get_last_record_by_experiment_id(
            "Search_space", experiment.unique_id
        )
        ss_size = ss_record["Search_space_size"] if ss_record else "Infinity"
        ss_is_finite = isinstance(ss_size, (int, float)) and math.isfinite(ss_size)

        for sc_config in sc_desc.get("Instance", {}).values():
            sc_type = sc_config.get("Type", "")
            if sc_type == "adaptive" and not ss_is_finite:
                print(f"Skipping AdaptiveType: search space is infinite")
                continue
            try:
                sc_class = reflective_class_import(
                    class_name=sc_type, folder_path="stop_condition"
                )
                sc = sc_class(sc_config, experiment.description, experiment.unique_id)
                scs.append(sc)
            except Exception as e:
                print(f"Skipped SC '{sc_type}': {e}")
                print_stack()
    except (KeyError, TypeError, AttributeError) as e:
        print(f"Failed to read StopCondition config: {e}")
        print_stack()
    return scs
