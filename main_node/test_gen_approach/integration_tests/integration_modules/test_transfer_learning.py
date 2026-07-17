import os

os.environ["TEST_MODE"] = "UNIT_TEST"

from copy import deepcopy

import numpy as np
import pytest

from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from core_entities.search_space import get_search_space_record
from configuration_selection.configuration_selection import ConfigurationSelection
from transfer_learning.transfer_learning_module import TransferLearningOrchestrator
from transfer_learning.model_recommendation.few_shot import FewShotRecommendation
from transfer_learning.transfer_expediency_determination.rgpe_comparator import RgpeComparator
from tools.initial_config import load_experiment_setup

from test_gen_approach.integration_tests.helpers.config_simulation import (
    add_configuration_to_experiment,
    assign_mock_results_to_configuration,
    get_mock_results_for_objectives,
    send_new_configurations,
    setup_default_configuration,
)

from test_gen_approach.integration_tests.helpers.experiment_utils import (
    create_configuration_selection,
    create_experiment_from_test_case,
    get_configuration_fixture_name,
    get_min_samples_for_tl,
    get_objective_count,
    get_parameter_types,
    has_transfer_learning,
    setup_task_configuration,
    write_experiment_to_db,
)

from test_gen_approach.integration_tests.helpers.db_utils import reset_database
from test_gen_approach.integration_tests.helpers.experiment_utils import (
    load_phase1_config,
    PHASE1_OUTPUT_DIR,
)

test_new_configs = True

_phase1_configs = sorted(f.name for f in PHASE1_OUTPUT_DIR.glob("*.json"))
_brise_test_cases = list(range(15))
_test_ids = _phase1_configs if test_new_configs else _brise_test_cases


def _load_experiment(test_id, get_experiment):
    if test_new_configs:
        exp_desc, search_space = load_phase1_config(test_id)
        if exp_desc is None or search_space is None:
            return None, None
        experiment = Experiment(exp_desc, search_space)
        Configuration.set_task_config(
            experiment.description["Context"]["TaskConfiguration"]
        )
        return experiment, search_space
    else:
        experiment, _, search_space = create_experiment_from_test_case(
            test_id, get_experiment
        )
        return experiment, search_space


# Path to the standard TL test case used by BRISE's own unit tests
_TEST_CASE_0 = "./Resources/tests/test_cases_product_configurations/test_case_0.json"

# Reusable TED block: NormDifference comparator, FixedQuantity=1 similar experiment
_NORM_DIFF_TED_FIXED = {
    "SamplingLandmarkBased": {
        "MinNumberOfSamples": 10,
        "Type": "sampling_landmark_based",
        "Comparator": {"NormDifference": {"Type": "norm_difference_comparator"}},
        "ExperimentsQuantity": {"FixedQuantity": {"NumberOfSimilarExperiments": 1}},
    }
}

def has_mtl_fsl(experiment) -> bool:
    tl = experiment.description.get("TransferLearning", {})
    mtl = tl.get("MultiTaskLearning", {})
    filters = mtl.get("Filters", {})
    return "FewShotMultiTask" in filters


class TestTransferLearning:
    @pytest.mark.parametrize("test_id", _test_ids)
    def test_tl_experiment_identified(self, test_id, get_experiment):
        reset_database()

        experiment, _ = _load_experiment(test_id, get_experiment)
        # if experiment is None:
        #     pytest.skip(f"Could not load config: {test_id}")
        assert experiment is not None

        is_tl = has_transfer_learning(experiment)

        if is_tl:
            assert (
                "TransferLearning" in experiment.description.keys()
            ), f"TL experiment missing TransferLearning key for: {test_id}"

    @pytest.mark.parametrize("test_id", _test_ids)
    def test_tl_min_samples_can_be_extracted(self, test_id, get_experiment):
        reset_database()

        experiment, _ = _load_experiment(test_id, get_experiment)
        # if experiment is None:
        #     pytest.skip(f"Could not load config: {test_id}")
        assert experiment is not None

        if not has_transfer_learning(experiment):
            pytest.skip(f"Config {test_id} is not a TL experiment")

        min_samples = get_min_samples_for_tl(experiment)

        assert (
            min_samples is not None
        ), f"Failed to extract MinNumberOfSamples for: {test_id}"
        assert isinstance(
            min_samples, int
        ), f"MinNumberOfSamples is not int for: {test_id}"
        assert (
            min_samples > 0
        ), f"MinNumberOfSamples should be positive for: {test_id}"

    @pytest.mark.parametrize("test_id", _test_ids)
    def test_tl_loop(
        self,
        test_id,
        get_experiment,
        get_workers,
        request,
        get_configurations_2_float,
        get_configurations_float_nom,
        get_configurations_all_types,
    ):
        reset_database()

        experiment, search_space = _load_experiment(test_id, get_experiment)
        # if experiment is None:
        #     pytest.skip(f"Could not load config: {test_id}")
        assert experiment is not None

        if not has_transfer_learning(experiment):
            pytest.skip(f"Config {test_id} is not a TL experiment")

        write_experiment_to_db(experiment, search_space)
        setup_task_configuration(experiment)

        parameter_types = get_parameter_types(experiment)
        fixture_name = get_configuration_fixture_name(parameter_types)
        config_fixture = request.getfixturevalue(fixture_name)
        objective_count = get_objective_count(experiment)

        setup_default_configuration(
            experiment, config_fixture, objective_count, is_transfer_learning=True
        )

        cs = create_configuration_selection(experiment)
        assert cs is not None

        min_samples = get_min_samples_for_tl(experiment)
        assert min_samples is not None

        configs = []

        for i in range(min_samples):
            predicted, _ = send_new_configurations(cs, get_workers)

            if predicted is None or len(predicted) == 0:
                print(f"{test_id}: Stopped at iteration {i}")
                break

            config = predicted[0]
            configs.append(config)

            assert (
                config.type == Configuration.Type.FROM_SELECTOR
            ), f"Landmark config {i} should be FROM_SELECTOR, got {config.type}"

            fixture_index = i % len(config_fixture)
            results = get_mock_results_for_objectives(
                config_fixture, fixture_index, objective_count
            )
            assign_mock_results_to_configuration(
                config, results, is_transfer_learning=True
            )
            add_configuration_to_experiment(
                experiment, config, is_transfer_learning=True
            )

        assert (
            len(configs) >= min_samples
        ), f"Expected {min_samples} configs, got {len(configs)} for: {test_id}"

    @pytest.mark.parametrize("test_id", _test_ids)
    def test_mtl_fsl_produces_transferred_best_config(
        self,
        test_id,
        get_experiment,
        get_workers,
        request,
        get_configurations_2_float,
        get_configurations_float_nom,
        get_configurations_all_types,
    ):
        reset_database()

        experiment, search_space = _load_experiment(test_id, get_experiment)
        # if experiment is None:
        #     pytest.skip(f"Could not load config: {test_id}")
        assert experiment is not None

        if not has_transfer_learning(experiment):
            pytest.skip(f"Config {test_id} is not a TL experiment")

        if not has_mtl_fsl(experiment):
            pytest.skip(f"Config {test_id} does not use MTL + Few-Shot")

        write_experiment_to_db(experiment, search_space)
        setup_task_configuration(experiment)

        parameter_types = get_parameter_types(experiment)
        fixture_name = get_configuration_fixture_name(parameter_types)
        config_fixture = request.getfixturevalue(fixture_name)
        objective_count = get_objective_count(experiment)

        setup_default_configuration(
            experiment, config_fixture, objective_count, is_transfer_learning=True
        )

        cs = create_configuration_selection(experiment)
        assert cs is not None

        min_samples = get_min_samples_for_tl(experiment)
        configs = []

        for i in range(min_samples):
            predicted, _ = send_new_configurations(cs, get_workers)
            assert (
                predicted is not None and len(predicted) > 0
            ), f"Failed to get config at iteration {i}"

            config = predicted[0]
            configs.append(config)

            fixture_index = i % len(config_fixture)
            results = get_mock_results_for_objectives(
                config_fixture, fixture_index, objective_count
            )
            assign_mock_results_to_configuration(
                config, results, is_transfer_learning=True
            )
            add_configuration_to_experiment(
                experiment, config, is_transfer_learning=True
            )

        predicted, _ = send_new_configurations(cs, get_workers)
        assert (
            predicted is not None and len(predicted) > 0
        ), "Failed to get best config"

        best_config = predicted[0]

        assert (
            best_config.type == Configuration.Type.TRANSFERRED
        ), f"MTL + FSL: Expected TRANSFERRED, got {best_config.type} for: {test_id}"


class TestTransferLearningUnit:

    def _load_experiment(self, skeleton=None):
        desc, ss = load_experiment_setup(_TEST_CASE_0)
        if skeleton is not None:
            desc = deepcopy(desc)
            desc.update(deepcopy(skeleton))
        experiment = Experiment(desc, ss)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        return experiment, ss

    def _write_to_db(self, experiment, search_space):
        experiment.database.write_one_record(
            "Experiment_description", experiment.get_experiment_description_record()
        )
        experiment.database.write_one_record(
            "Search_space", get_search_space_record(search_space, experiment.unique_id)
        )

    def _run_measurement_iterations(self, cs, experiment, configs_fixture, get_workers, n=10):
        predicted, _ = cs.send_new_configurations_to_measure("", "", "", get_workers)
        results = configs_fixture[0]["Result"]
        del results["Y3"]
        del results["Y4"]
        del results["Y5"]
        predicted[0].results = results
        predicted[0].status["measured"] = True
        predicted[0].status["evaluated"] = True
        experiment.default_configuration = predicted[0]

        for i in range(1, n):
            predicted, _ = cs.send_new_configurations_to_measure("", "", "", get_workers)
            results = configs_fixture[i]["Result"]
            del results["Y3"]
            del results["Y4"]
            del results["Y5"]
            predicted[0].results = results
            predicted[0].status["measured"] = True
            predicted[0].status["evaluated"] = True
            experiment.measured_configurations.append(predicted[0])
            experiment.database.write_one_record(
                "Configuration", predicted[0].get_configuration_record()
            )
            experiment.send_state_to_db()

    def test_dynamic_model_recommendation_hard_threshold(
        self, get_workers, get_configurations_2_float
    ):
        reset_database()
        experiment, search_space = self._load_experiment()
        self._write_to_db(experiment, search_space)
        cs = ConfigurationSelection(experiment)
        tl = TransferLearningOrchestrator(
            experiment_id=experiment.unique_id,
            experiment_description=experiment.description,
        )
        self._run_measurement_iterations(cs, experiment, get_configurations_2_float, get_workers)
        similar_experiments = tl.ted_module.analyse_experiments_similarity()
        mapping = tl.transfer_submodules["Model_transfer"].recommend_best_model(similar_experiments)
        assert mapping is not None

    def test_dynamic_model_recommendation_soft_threshold(
        self, get_workers, get_configurations_2_float
    ):
        reset_database()
        skeleton = {
            "TransferLearning": {
                "TransferExpediencyDetermination": _NORM_DIFF_TED_FIXED,
                "ModelRecommendation": {
                    "DynamicModelsRecommendation": {
                        "RecommendationGranularity": {"Infinite": {"Value": np.inf}},
                        "PerformanceMetric": {
                            "AverageRelativeImprovement": {
                                "Type": "average_relative_improvement"
                            }
                        },
                        "Type": "dynamic_model_recommendation",
                        "ThresholdType": "Soft",
                        "TimeToBuildModelThreshold": 0.01,
                        "TimeUnit": "seconds",
                    }
                },
            }
        }
        experiment, search_space = self._load_experiment(skeleton)
        self._write_to_db(experiment, search_space)
        cs = ConfigurationSelection(experiment)
        tl = TransferLearningOrchestrator(
            experiment_id=experiment.unique_id,
            experiment_description=experiment.description,
        )
        self._run_measurement_iterations(cs, experiment, get_configurations_2_float, get_workers)
        similar_experiments = tl.ted_module.analyse_experiments_similarity()
        mapping = tl.transfer_submodules["Model_transfer"].recommend_best_model(similar_experiments)
        assert mapping is not None

    def test_few_shot_model_recommendation(self, get_workers, get_configurations_2_float):
        reset_database()
        skeleton = {
            "TransferLearning": {
                "TransferExpediencyDetermination": _NORM_DIFF_TED_FIXED,
                "ModelRecommendation": {"FewShotRecommendation": {"Type": "few_shot"}},
            }
        }
        experiment, _ = self._load_experiment(skeleton)
        cs = ConfigurationSelection(experiment)
        tl = TransferLearningOrchestrator(
            experiment_id=experiment.unique_id,
            experiment_description=experiment.description,
        )
        self._run_measurement_iterations(cs, experiment, get_configurations_2_float, get_workers)
        similar_experiments = tl.ted_module.analyse_experiments_similarity()
        mapping = tl.transfer_submodules["Model_transfer"].recommend_best_model(similar_experiments)
        assert mapping is not None

    def test_few_shot_were_models_dumped(self):
        assert FewShotRecommendation.were_models_dumped([]) is False
        assert FewShotRecommendation.were_models_dumped([None]) is False
        assert FewShotRecommendation.were_models_dumped([b"serialised_model"]) is True

    def test_rgpe_comparator(self, get_workers, get_configurations_2_float):
        reset_database()
        skeleton = {
            "TransferLearning": {
                "TransferExpediencyDetermination": {
                    "SamplingLandmarkBased": {
                        "MinNumberOfSamples": 10,
                        "Type": "sampling_landmark_based",
                        "Comparator": {"RGPE": {"Type": "rgpe_comparator"}},
                        "ExperimentsQuantity": {
                            "FixedQuantity": {"NumberOfSimilarExperiments": 1}
                        },
                    }
                },
            }
        }
        experiment, _ = self._load_experiment(skeleton)
        cs = ConfigurationSelection(experiment)
        tl = TransferLearningOrchestrator(
            experiment_id=experiment.unique_id,
            experiment_description=experiment.description,
        )
        assert isinstance(tl.ted_module.comparator, RgpeComparator)
        self._run_measurement_iterations(cs, experiment, get_configurations_2_float, get_workers)
        similar_experiments = tl.ted_module.analyse_experiments_similarity()
        assert len(similar_experiments) >= 1

    def test_mean_shift_clustering_fixed_bandwidth(self, get_workers, get_configurations_2_float):
        reset_database()
        skeleton = {
            "TransferLearning": {
                "TransferExpediencyDetermination": {
                    "SamplingLandmarkBased": {
                        "MinNumberOfSamples": 10,
                        "Type": "sampling_landmark_based",
                        "Comparator": {"NormDifference": {"Type": "norm_difference_comparator"}},
                        "ExperimentsQuantity": {
                            "AdaptiveQuantity": {
                                "Clustering": {
                                    "MeanShift": {
                                        "Type": "mean_shift_clustering",
                                        "BandwidthType": "Fixed",
                                        "bandwidth": 0.3,
                                        "quantile": 0.3,
                                    }
                                }
                            }
                        },
                    }
                },
            }
        }
        experiment, _ = self._load_experiment(skeleton)
        cs = ConfigurationSelection(experiment)
        tl = TransferLearningOrchestrator(
            experiment_id=experiment.unique_id,
            experiment_description=experiment.description,
        )
        self._run_measurement_iterations(cs, experiment, get_configurations_2_float, get_workers)
        similar_experiments = tl.ted_module.analyse_experiments_similarity()
        assert len(similar_experiments) >= 1

    def test_mean_shift_clustering_estimated_bandwidth(
        self, get_workers, get_configurations_2_float
    ):
        reset_database()
        skeleton = {
            "TransferLearning": {
                "TransferExpediencyDetermination": {
                    "SamplingLandmarkBased": {
                        "MinNumberOfSamples": 10,
                        "Type": "sampling_landmark_based",
                        "Comparator": {"NormDifference": {"Type": "norm_difference_comparator"}},
                        "ExperimentsQuantity": {
                            "AdaptiveQuantity": {
                                "Clustering": {
                                    "MeanShift": {
                                        "Type": "mean_shift_clustering",
                                        "BandwidthType": "Estimated",
                                        "bandwidth": -1.0,
                                        "quantile": 0.3,
                                    }
                                }
                            }
                        },
                    }
                },
            }
        }
        experiment, _ = self._load_experiment(skeleton)
        cs = ConfigurationSelection(experiment)
        tl = TransferLearningOrchestrator(
            experiment_id=experiment.unique_id,
            experiment_description=experiment.description,
        )
        self._run_measurement_iterations(cs, experiment, get_configurations_2_float, get_workers)
        similar_experiments = tl.ted_module.analyse_experiments_similarity()
        assert len(similar_experiments) >= 1

    def test_only_best_mtl(self, get_workers, get_configurations_2_float):
        reset_database()
        skeleton = {
            "TransferLearning": {
                "TransferExpediencyDetermination": _NORM_DIFF_TED_FIXED,
                "MultiTaskLearning": {
                    "Filters": {"OnlyBestConfigurations": {"Type": "only_best"}}
                },
            }
        }
        experiment, _ = self._load_experiment(skeleton)
        cs = ConfigurationSelection(experiment)
        tl = TransferLearningOrchestrator(
            experiment_id=experiment.unique_id,
            experiment_description=experiment.description,
        )
        self._run_measurement_iterations(cs, experiment, get_configurations_2_float, get_workers)
        similar_experiments = tl.ted_module.analyse_experiments_similarity()
        transferred_configs = tl.transfer_submodules["Configuration_transfer"].transfer_configurations(
            similar_experiments
        )
        assert len(transferred_configs) > 0
