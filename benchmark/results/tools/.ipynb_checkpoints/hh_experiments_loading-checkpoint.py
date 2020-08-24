__doc__ = """ this module is only for temporal usage for analysing Hyper-heuristic experiments.
Later, functionality will be merged to analyse part of benchmark (currently in repeater benchmark branch).
"""

import pandas as pd
import os
import pickle
import hashlib
import json

from copy import deepcopy
from collections import OrderedDict

from core_entities.experiment import Experiment
from core_entities.configuration import Configuration
from tools.initial_config import load_experiment_setup


def ed_to_id(experiment_description: dict) -> str:
    return hashlib.sha1(json.dumps(experiment_description, sort_keys=True).encode("utf-8")).hexdigest()


def load_exp(filename: str) -> Experiment:
    with open(filename, 'rb') as f:
        return pickle.load(f)


def exp_progress_loader(exp: Experiment) -> pd.DataFrame:
    data = []
    current_best: Configuration = exp.measured_configurations[0]
    results = current_best.results
    results['iteration'] = 0
    data.append(results)
    for cfg_idx, cfg in enumerate(exp.measured_configurations[1:]):
        if cfg.is_enabled and cfg.results['objective'] < current_best.results['objective']:
            current_best = cfg
        results = current_best.results
        results['iteration'] = cfg_idx + 1
        data.append(results)
    df = pd.DataFrame(data)
    df['Mode'] = exp.description["DomainDescription"]["DataFile"][exp.description["DomainDescription"]["DataFile"].rfind("/") +1 :
                                                                 exp.description["DomainDescription"]["DataFile"].rfind("Data")]
    return df


def exp_chronics_loader(exp: Experiment) -> pd.DataFrame:
    data = []
    for cfg_idx, cfg in enumerate(exp.measured_configurations):
        results = cfg.to_series()
        results['iteration'] = cfg_idx
        data.append(results)
    return pd.DataFrame(data)


def load_tsp_results(results_storage: str, loader: callable) -> (pd.DataFrame, pd.DataFrame):
    mab_model = {
        "Type": "brise.MultiArmedBandit",
        "Parameters": {
            "objectives_minimization": {"improvement": False},
            "c": "std"
        }
    }
    tpe_model = {
        "Type": "brise.TreeParzenEstimator",
        "Parameters": {
            "top_n_percent": 30,
            "random_fraction": 0,
            "bandwidth_factor": 3,
            "min_bandwidth": 0.001,
            "objectives_minimization": {"improvement": False},
            "SamplingSize": 96
        }
    }
    sklearn_bo_model = {
        "Type": "sklearn.BayesianRidge",
        "Parameters": {
            "SamplingSize": 96,
            "MinimalScore": 0.5,
            "CrossValidationSplits": 5,
            "TestSize": 0.30,
            "objectives_minimization": {"improvement": False},
            "DataPreprocessing": {
                "OrdinalHyperparameter": "sklearn.OrdinalEncoder",
                "NominalHyperparameter": "brise.BinaryEncoder",
                "IntegerHyperparameter": "sklearn.MinMaxScaler",
                "FloatHyperparameter": "sklearn.MinMaxScaler"
            },
            "UnderlyingModelParameters": {}
        }
    }
    random_model = {
        "Type": "brise.ModelMock",
        "Parameters": {"objectives_minimization": {"improvement": False}, }
    }

    # --- benchmark scenario description
    ed_paths = OrderedDict({
        "jMetalPy.SA": "./Resources/HyperHeuristic/MHjMetalPySAExperiment.json",  # only jMetalPy SA
        "jMetalPy.ES": "./Resources/HyperHeuristic/MHjMetalPyESExperiment.json",  # only jMetalPy ES
        "jMetal.ES": "./Resources/HyperHeuristic/MHjMetalESExperiment.json",  # only jMetal ES
        "HH": "./Resources/HyperHeuristic/HHExperiment.json",  # hyper-heuristic (SA + ES + ES)
    })

    scenarios = OrderedDict({
        # --- BASELINE. STATIC Meta-heuristics + STATIC hyperparameters (default or optimized).
        "static LLH, default hyperparameters": {
            "ExperimentDescriptions": [ed_paths['jMetalPy.ES'], ed_paths['jMetalPy.SA'], ed_paths['jMetal.ES']],
            "Models": [random_model],
            "Hyperparameters": "default",
            "Codes": ["4.1.1", "4.2.1", "4.3.1"]
        },
        "static LLH, tuned hyperparameters": {
            "ExperimentDescriptions": [ed_paths['jMetalPy.ES'], ed_paths['jMetalPy.SA'], ed_paths['jMetal.ES']],
            "Models": [random_model],
            "Hyperparameters": "tuned",
            "Codes": ["4.1.2", "4.2.2", "4.3.2"]
        },
        # --- Parameter control in LLH (MHs)
        "static LLH, random hyperparameters": {
            "ExperimentDescriptions": [ed_paths['jMetalPy.ES'], ed_paths['jMetalPy.SA'], ed_paths['jMetal.ES']],
            "Models": [random_model],
            "Hyperparameters": "provided",
            "Codes": ["4.1.3", "4.2.3", "4.3.3"]
        },
        "static LLH, tpe_model hyperparameters": {
            "ExperimentDescriptions": [ed_paths['jMetalPy.ES'], ed_paths['jMetalPy.SA'], ed_paths['jMetal.ES']],
            "Models": [random_model, tpe_model],
            "Hyperparameters": "provided",
            "Codes": ["4.1.4", "4.2.4", "4.3.4"]
        },
        "static LLH, sklearn_bo_model hyperparameters": {
            "ExperimentDescriptions": [ed_paths['jMetalPy.ES'], ed_paths['jMetalPy.SA'], ed_paths['jMetal.ES']],
            "Models": [random_model, sklearn_bo_model],
            "Hyperparameters": "provided",
            "Codes": ["4.1.5", "4.2.5", "4.3.5"]
        },
        # --- Hyper-heuristics with STATIC hyperparameters
        "random LLH, default hyperparameters": {
            "ExperimentDescriptions": [ed_paths['HH']],
            "Models": [random_model],
            "Hyperparameters": "default",
            "Codes": ["1.1."]
        },
        "random LLH, tuned hyperparameters": {
            "ExperimentDescriptions": [ed_paths['HH']],
            "Models": [random_model],
            "Hyperparameters": "tuned",
            "Codes": ["1.2."]
        },
        "mab_model LLH, default hyperparameters": {
            "ExperimentDescriptions": [ed_paths['HH']],
            "Models": [mab_model, random_model],
            "Hyperparameters": "default",
            "Codes": ["2.1."]
        },
        "mab_model LLH, tuned hyperparameters": {
            "ExperimentDescriptions": [ed_paths['HH']],
            "Models": [mab_model, random_model],
            "Hyperparameters": "tuned",
            "Codes": ["2.2."]
        },
        "sklearn_bo_model LLH, default hyperparameters": {
            "ExperimentDescriptions": [ed_paths['HH']],
            "Models": [sklearn_bo_model, random_model],
            "Hyperparameters": "default",
            "Codes": ["3.1."]
        },
        "sklearn_bo_model LLH, tuned hyperparameters": {
            "ExperimentDescriptions": [ed_paths['HH']],
            "Models": [sklearn_bo_model, random_model],
            "Hyperparameters": "tuned",
            "Codes": ["3.2."]
        },
        # --- Hyper-heuristics with DYNAMIC hyperparameters
        "random LLH, random hyperparameters": {
            "ExperimentDescriptions": [ed_paths['HH']],
            "Models": [random_model],
            "Hyperparameters": "provided",
            "Codes": ["1.3."]
        },
        "mab_model LLH, tpe_model hyperparameters": {
            "ExperimentDescriptions": [ed_paths['HH']],
            "Models": [mab_model, tpe_model],
            "Hyperparameters": "provided",
            "Codes": ["2.4."]
        },
        "mab_model LLH, sklearn_bo_model hyperparameters": {
            "ExperimentDescriptions": [ed_paths['HH']],
            "Models": [mab_model, sklearn_bo_model],
            "Hyperparameters": "provided",
            "Codes": ["2.5."]
        },
        "sklearn_bo_model LLH, tpe_model hyperparameters": {
            "ExperimentDescriptions": [ed_paths['HH']],
            "Models": [sklearn_bo_model, tpe_model],
            "Hyperparameters": "provided",
            "Codes": ["3.4."]
        },
        "sklearn_bo_model LLH, sklearn_bo_model hyperparameters": {
            "ExperimentDescriptions": [ed_paths['HH']],
            "Models": [sklearn_bo_model, sklearn_bo_model],
            "Hyperparameters": "provided",
            "Codes": ["3.5."]
        }
    })
    # Will be used for full benchmark.
    tsp_problems = [
        "kroA100.tsp",
        "pr439.tsp",
        "rat783.tsp",
        "pla7397.tsp",
    ]

    instances_optimums = {
        "eil51.tsp": 426,
        "kroA100.tsp": 21282,
        "kroA150.tsp": 26524,
        "kroB200.tsp": 29437,
        "pr439.tsp": 107217,
        "rat783.tsp": 8806,
        "pla7397.tsp": 23260728,
        "d15112.tsp": 1573084
    }

    scenario_groups = {
        # Meta-Heuristics (baseline)
        "4.1.1": "MH",
        "4.2.1": "MH",
        "4.3.1": "MH",
        "4.1.2": "MH",
        "4.2.2": "MH",
        "4.3.2": "MH",
        # Parameter Control in Meta-Heuristics
        "4.1.3": "MH-PC",
        "4.2.3": "MH-PC",
        "4.3.3": "MH-PC",
        "4.1.4": "MH-PC",
        "4.2.4": "MH-PC",
        "4.3.4": "MH-PC",
        "4.1.5": "MH-PC",
        "4.2.5": "MH-PC",
        "4.3.5": "MH-PC",
        # Hyper-Heuristics with static hyperparameters
        "1.1.": "HH-SP",
        "1.2.": "HH-SP",
        "2.1.": "HH-SP",
        "2.2.": "HH-SP",
        "3.1.": "HH-SP",
        "3.2.": "HH-SP",
        # Hyper-Heuristics with dynamic hyperparameters
        "1.3.": "HH-PC",
        "2.4.": "HH-PC",
        "2.5.": "HH-PC",
        "3.4.": "HH-PC",
        "3.5.": "HH-PC"
    }

    files = os.listdir(results_storage)

    # > differentiating tsp-instances
    all_processes = pd.DataFrame()
    all_final_results = pd.DataFrame()

    for tsp_instance in tsp_problems:
        per_instance_progress = pd.DataFrame()
        per_instance_final_results = pd.DataFrame()

        # >> differentiating scenarios (prediction models used)
        for sc_name, sc_desc in scenarios.items():
            per_scenario_progress = pd.DataFrame()
            per_scenario_final_results = pd.DataFrame()

            # >>> differentiating concrete modes (ES, SA, GA or HH) within scenario
            for ed_path_idx, ed_path in enumerate(sc_desc["ExperimentDescriptions"]):
                per_mode_progress = pd.DataFrame()
                per_mode_final_results = pd.DataFrame()

                # Deriving the Experiment ID
                base_experiment_description, _ = load_experiment_setup(ed_path)
                experiment_description = deepcopy(base_experiment_description)
                experiment_description["Predictor"]["models"] = sc_desc["Models"]
                experiment_description["TaskConfiguration"]["Scenario"]["Hyperparameters"] = sc_desc[
                    "Hyperparameters"]
                experiment_description["TaskConfiguration"]["Scenario"]["problem_initialization_parameters"][
                    "instance"] = "scenarios/tsp/" + tsp_instance
                id_ = ed_to_id(experiment_description)

                # Now we have an ID of Experiment
                # Those, we load all repetitions of this Experiment.
                experiment_dumps = list(filter(lambda f_name: id_ in f_name, files))
                for repetition, exp_dump_name in enumerate(experiment_dumps):
                    repetition_progress = loader(load_exp(results_storage + exp_dump_name))
                    repetition_final_results = repetition_progress.iloc[-1]

                    repetition_progress['Repetition'] = repetition
                    repetition_final_results['Repetition'] = repetition
                    per_mode_progress = per_mode_progress.append(repetition_progress, sort=False)
                    per_mode_final_results = per_mode_final_results.append(repetition_final_results, sort=False)

                experiment_code = sc_desc["Codes"][ed_path_idx]
                per_mode_progress["Code"] = experiment_code
                per_mode_final_results["Code"] = experiment_code
                per_mode_progress["Experiment Group"] = scenario_groups[experiment_code]
                per_mode_final_results["Experiment Group"] = scenario_groups[experiment_code]

                per_scenario_progress = per_scenario_progress.append(per_mode_progress, sort=False)
                per_scenario_final_results = per_scenario_final_results.append(per_mode_final_results, sort=False)
                per_scenario_final_results["ID"] = id_
                

            per_instance_progress = per_instance_progress.append(per_scenario_progress, sort=False)
            per_instance_final_results = per_instance_final_results.append(per_scenario_final_results, sort=False)

        per_instance_progress["TSP instance"] = tsp_instance
        per_instance_progress["Optimum"] = instances_optimums[tsp_instance]
        per_instance_final_results["TSP instance"] = tsp_instance
        per_instance_final_results["Optimum"] = instances_optimums[tsp_instance]
        all_processes = all_processes.append(per_instance_progress, sort=False)
        all_final_results = all_final_results.append(per_instance_final_results, sort=False)

    return all_processes, all_final_results

if __name__ == '__main__':
    new_processes, new_final_results = load_tsp_results("dumps/bench1_instancewise/", exp_progress_loader)