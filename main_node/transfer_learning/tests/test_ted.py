from typing import Tuple, Dict
from copy import deepcopy

from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from core_entities.search_space import SearchSpace
from tools.initial_config import load_experiment_setup
from tools.restore_db import RestoreDB
from configuration_selection.configuration_selection import ConfigurationSelection
from transfer_learning.transfer_learning_module import TransferLearningOrchestrator
from transfer_learning.transfer_expediency_determination.rgpe_comparator import RgpeComparator
from transfer_learning.transfer_expediency_determination.norm_difference_comparator import NormDifferenceComparator
from transfer_learning.transfer_expediency_determination.clustering.mean_shift_clustering import MeanShift

experiment_description_file = "./Resources/tests/test_cases_product_configurations/test_case_0.json"
rdb = RestoreDB()


class TestTED:
    def test_0(self):
        """empty db"""
        rdb.cleanup()
        experiment, search_space = self.initialize_exeriment(experiment_description_file)
        assert "Transfer_learning_info" not in experiment.database.database.list_collection_names()

    def test_1(self, get_workers, get_energy_configurations):
        """no similar experiment found. Target energy. Source test experiments"""
        rdb.restore()
        experiment_description_file = "./Resources/tests/test_cases_product_configurations/EnergyExperimentWithTL.json"
        experiment, search_space = self.initialize_exeriment(experiment_description_file)
        cs = ConfigurationSelection(experiment)
        predicted, measured = cs.send_new_configurations_to_measure("","","", get_workers)
        results = get_energy_configurations[0]['Result']
        predicted[0].results = results
        predicted[0].status['measured'] = True
        predicted[0].status['evaluated'] = True
        experiment.default_configuration = predicted[0]
        for i in range(1, 10):
            predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)

            results = get_energy_configurations[i]['Result']
            predicted[0].results = results
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True

            experiment.measured_configurations.append(predicted[0])
            experiment.database.write_one_record("Configuration", predicted[0].get_configuration_record())
            experiment.send_state_to_db()

        tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id,
                                          experiment_description=experiment.description)
        assert len(tl.ted_module.analyse_experiments_similarity()) == 0

    def test_2(self, get_workers, get_configurations_2_float):
        """similar experiment found"""
        experiment, search_space = self.initialize_exeriment(experiment_description_file)
        cs = ConfigurationSelection(experiment)
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

        tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id,
                                          experiment_description=experiment.description)
        assert len(tl.ted_module.analyse_experiments_similarity()) == 1

    def test_3(self, get_workers, get_configurations_2_float):
        """similar experiment found"""
        rgpe_skeleton = {
            "TransferLearning": {
                "TransferExpediencyDetermination": {
                    "SamplingLandmarkBased": {
                        "MinNumberOfSamples": 10,
                        "Type": "sampling_landmark_based",
                        "Comparator": {
                            "RGPE": {
                                "Type": "rgpe_comparator"
                            }
                        },
                        "ExperimentsQuantity": {
                            "FixedQuantity": {
                                "NumberOfSimilarExperiments": 1
                            }
                        }
                    }
                }
            }
        }
        experiment, search_space = self.initialize_exeriment(experiment_description_file, rgpe_skeleton)
        cs = ConfigurationSelection(experiment)
        tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id,
                                          experiment_description=experiment.description)
        assert isinstance(tl.ted_module.comparator, RgpeComparator)
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

        assert len(tl.ted_module.analyse_experiments_similarity()) == 1

    def test_4(self, get_workers, get_configurations_2_float):
        """similar experiment found"""
        clustering_skeleton = {
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
                            "AdaptiveQuantity": {
                                "Clustering": {
                                    "MeanShift": {
                                        "Type": "mean_shift_clustering",
                                        "BandwidthType": "Fixed",
                                        "bandwidth": 0.3,
                                        "quantile": 0.3
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        experiment, search_space = self.initialize_exeriment(experiment_description_file, clustering_skeleton)
        cs = ConfigurationSelection(experiment)
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

        tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id,
                                          experiment_description=experiment.description)
        assert len(tl.ted_module.analyse_experiments_similarity()) == 1

    def test_5(self, get_workers, get_configurations_2_float):
        """similar experiment found"""
        clustering_skeleton = {
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
                            "AdaptiveQuantity": {
                                "Clustering": {
                                    "MeanShift": {
                                        "Type": "mean_shift_clustering",
                                        "BandwidthType": "Estimated",
                                        "bandwidth": -1.0,
                                        "quantile": 0.3
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        experiment, search_space = self.initialize_exeriment(experiment_description_file, clustering_skeleton)
        cs = ConfigurationSelection(experiment)
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

        tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id,
                                          experiment_description=experiment.description)
        assert len(tl.ted_module.analyse_experiments_similarity()) == 1

    def test_ban_experiments_decrements_cache_rather_than_clearing_it(self, get_workers, get_configurations_float_nom):
        """
        test_case_4.json + get_configurations_float_nom deterministically surfaces two similar source
        experiments (matching F/N parameter keys). Banning one must leave the other cached, not force a
        full re-run of the comparator.
        """
        rdb.cleanup()
        rdb.restore()
        experiment_description_file_4 = "./Resources/tests/test_cases_product_configurations/test_case_4.json"
        experiment, search_space = self.initialize_exeriment(experiment_description_file_4)
        cs = ConfigurationSelection(experiment)
        predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
        results = {"Y1": get_configurations_float_nom[0]['Result']["Y1"]}
        predicted[0].results = results
        predicted[0].status['measured'] = True
        predicted[0].status['evaluated'] = True
        experiment.default_configuration = predicted[0]

        for i in range(1, 10):
            predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
            results = {"Y1": get_configurations_float_nom[i]['Result']["Y1"]}
            predicted[0].results = results
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True
            experiment.measured_configurations.append(predicted[0])
            experiment.database.write_one_record("Configuration", predicted[0].get_configuration_record())
            experiment.send_state_to_db()

        tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id,
                                          experiment_description=experiment.description)
        similar = tl.ted_module.analyse_experiments_similarity()
        assert len(similar) == 2
        first_id, second_id = similar[0]["Exp_unique_ID"], similar[1]["Exp_unique_ID"]

        call_count = {"n": 0}
        original_get_similar_experiments = tl.ted_module.comparator.get_similar_experiments

        def counting_get_similar_experiments(*args, **kwargs):
            call_count["n"] += 1
            return original_get_similar_experiments(*args, **kwargs)
        tl.ted_module.comparator.get_similar_experiments = counting_get_similar_experiments

        tl.ted_module.ban_experiments([first_id])
        assert [e["Exp_unique_ID"] for e in tl.ted_module.similar_experiments] == [second_id]

        result = tl.ted_module.analyse_experiments_similarity()
        assert [e["Exp_unique_ID"] for e in result] == [second_id]
        assert call_count["n"] == 0, "banning one source should not force the comparator to re-run"

    def test_ban_experiments_exhausts_to_empty_when_no_source_remains(self, get_workers, get_configurations_2_float):
        """
        test_case_0.json + get_configurations_2_float is the same pairing test_2 uses, where exactly one
        source experiment is similar. Banning it must leave analyse_experiments_similarity returning the
        honest empty list, not raise or silently keep offering it.
        """
        rdb.cleanup()
        rdb.restore()
        experiment, search_space = self.initialize_exeriment(experiment_description_file)
        cs = ConfigurationSelection(experiment)
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

        tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id,
                                          experiment_description=experiment.description)
        similar = tl.ted_module.analyse_experiments_similarity()
        assert len(similar) == 1

        tl.ted_module.ban_experiments([similar[0]["Exp_unique_ID"]])
        assert tl.ted_module.analyse_experiments_similarity() == []

    def initialize_exeriment(self, experiment_description_file: str, skeleton: Dict = None) -> Tuple[Experiment, SearchSpace]:
        experiment_description, search_space = load_experiment_setup(experiment_description_file)

        modified_description = experiment_description
        if skeleton is not None:
            modified_description = deepcopy(experiment_description)
            modified_description.update(deepcopy(skeleton))

        experiment = Experiment(modified_description, search_space)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        return experiment, search_space
