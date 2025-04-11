from typing import Dict, Tuple
from copy import deepcopy

import numpy as np

from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from core_entities.search_space import SearchSpace, get_search_space_record
from configuration_selection.configuration_selection import ConfigurationSelection
from configuration_selection.model.surrogate.tree_parzen_estimator import TreeParzenEstimator
from transfer_learning.transfer_learning_module import TransferLearningOrchestrator
from sklearn.gaussian_process import GaussianProcessRegressor
from tools.initial_config import load_experiment_setup
from tools.restore_db import RestoreDB


experiment_description_file = "./Resources/tests/test_cases_product_configurations/test_case_0.json"
rdb = RestoreDB()


class TestMR:
    def test_0(self, get_workers, get_configurations_2_float):
        """
        dynamic model recommendation
        """
        rdb.cleanup()
        rdb.restore()
        experiment, search_space = self.initialize_experiment()
        experiment.database.write_one_record("Experiment_description", experiment.get_experiment_description_record())
        experiment.database.write_one_record(
            "Search_space", get_search_space_record(search_space, experiment.unique_id)
        )

        cs = ConfigurationSelection(experiment)
        tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id,
                                          experiment_description=experiment.description)
        predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
        results = get_configurations_2_float[0]['Result']
        del results["Y3"]
        del results["Y4"]
        del results["Y5"]
        predicted[0].results = results
        predicted[0].status['measured'] = True
        predicted[0].status['evaluated'] = True
        experiment.default_configuration = predicted[0]

        for i in range(1, 10):
            predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)

            results = get_configurations_2_float[i]['Result']
            del results["Y3"]
            del results["Y4"]
            del results["Y5"]
            predicted[0].results = results
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True

            experiment.measured_configurations.append(predicted[0])
            experiment.database.write_one_record("Configuration", predicted[0].get_configuration_record())
            experiment.send_state_to_db()

        similar_experiments = tl.ted_module.analyse_experiments_similarity()

        mapping_region_model = tl.transfer_submodules["Model_transfer"].recommend_best_model(similar_experiments)
        region = list(mapping_region_model.keys())[0]
        isinstance(region, Tuple)
        surrogate = list(mapping_region_model[region].mapping_surrogate_objective.keys())[0]
        assert isinstance(surrogate.surrogate_instance, GaussianProcessRegressor)

    def test_1(self, get_workers, get_configurations_2_float):
        """
        soft quality constraint
        """
        rdb.restore()

        soft_constraint_skeleton = {
            "TransferLearning": {
                "TransferExpediencyDetermination": {
                    "SamplingLandmarkBased": {
                        "MinNumberOfSamples": 10,
                        "Type": "sampling_landmark_based",
                        "Comparator": {
                            "NormDifference": {
                                "Type": "norm_difference_comparator"
                            }
                        },
                        "ExperimentsQuantity": {
                            "FixedQuantity": {
                                "NumberOfSimilarExperiments": 1
                            }
                        }
                    }
                },
                "ModelRecommendation": {
                    "DynamicModelsRecommendation": {
                        "RecommendationGranularity": {
                            "Infinite": {
                                "Value": np.inf
                            }
                        },
                        "PerformanceMetric": {
                            "AverageRelativeImprovement": {}
                        },
                        "Type": "dynamic_model_recommendation",
                        "ThresholdType": "Soft",
                        "TimeToBuildModelThreshold": 0.01,
                        "TimeUnit": "seconds"
                    }
                }
            }
        }

        experiment, search_space = self.initialize_experiment(soft_constraint_skeleton)
        experiment.database.write_one_record("Experiment_description", experiment.get_experiment_description_record())
        experiment.database.write_one_record(
            "Search_space", get_search_space_record(search_space, experiment.unique_id)
        )

        cs = ConfigurationSelection(experiment)
        tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id,
                                          experiment_description=experiment.description)
        predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
        results = get_configurations_2_float[0]['Result']
        del results["Y3"]
        del results["Y4"]
        del results["Y5"]
        predicted[0].results = results
        predicted[0].status['measured'] = True
        predicted[0].status['evaluated'] = True
        experiment.default_configuration = predicted[0]

        for i in range(1, 10):
            predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)

            results = get_configurations_2_float[i]['Result']
            del results["Y3"]
            del results["Y4"]
            del results["Y5"]
            predicted[0].results = results
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True

            experiment.measured_configurations.append(predicted[0])
            experiment.database.write_one_record("Configuration", predicted[0].get_configuration_record())
            experiment.send_state_to_db()

        similar_experiments = tl.ted_module.analyse_experiments_similarity()

        mapping_region_model = tl.transfer_submodules["Model_transfer"].recommend_best_model(similar_experiments)
        assert mapping_region_model is not None

    def test_2(self, get_workers, get_configurations_2_float):
        """
        few shot
        """
        rdb.restore()

        few_shot_skeleton = {
            "TransferLearning": {
                "TransferExpediencyDetermination": {
                    "SamplingLandmarkBased": {
                        "MinNumberOfSamples": 10,
                        "Type": "sampling_landmark_based",
                        "Comparator": {
                            "NormDifference": {
                                "Type": "norm_difference_comparator"
                            }
                        },
                        "ExperimentsQuantity": {
                            "FixedQuantity": {
                                "NumberOfSimilarExperiments": 1
                            }
                        }
                    }
                },
                "ModelRecommendation": {
                    "FewShotRecommendation": {
                        "Type": "few_shot"
                    }
                }
            }
        }
        experiment, search_space = self.initialize_experiment(few_shot_skeleton)
        cs = ConfigurationSelection(experiment)
        tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id,
                                          experiment_description=experiment.description)
        predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
        results = get_configurations_2_float[0]['Result']
        del results["Y3"]
        del results["Y4"]
        del results["Y5"]
        predicted[0].results = results
        predicted[0].status['measured'] = True
        predicted[0].status['evaluated'] = True
        experiment.default_configuration = predicted[0]

        for i in range(1, 10):
            predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)

            results = get_configurations_2_float[i]['Result']
            del results["Y3"]
            del results["Y4"]
            del results["Y5"]
            predicted[0].results = results
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True

            experiment.measured_configurations.append(predicted[0])
            experiment.database.write_one_record("Configuration", predicted[0].get_configuration_record())
            experiment.send_state_to_db()

        similar_experiments = tl.ted_module.analyse_experiments_similarity()

        mapping_region_model = tl.transfer_submodules["Model_transfer"].recommend_best_model(similar_experiments)
        region = list(mapping_region_model.keys())[0]
        isinstance(region, Tuple)
        surrogate = list(mapping_region_model[region].mapping_surrogate_objective.keys())[0]
        assert isinstance(surrogate.surrogate_instance, GaussianProcessRegressor)

    def initialize_experiment(self, skeleton: Dict = None) -> Tuple[Experiment, SearchSpace]:
        experiment_description, search_space = load_experiment_setup(experiment_description_file)

        modified_description = experiment_description
        if skeleton is not None:
            modified_description = deepcopy(experiment_description)
            modified_description.update(deepcopy(skeleton))

        experiment = Experiment(modified_description, search_space)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        return experiment, search_space
