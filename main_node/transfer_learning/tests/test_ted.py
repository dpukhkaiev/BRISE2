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

    def initialize_exeriment(self, experiment_description_file: str, skeleton: Dict = None) -> Tuple[Experiment, SearchSpace]:
        experiment_description, search_space = load_experiment_setup(experiment_description_file)

        modified_description = experiment_description
        if skeleton is not None:
            modified_description = deepcopy(experiment_description)
            modified_description.update(deepcopy(skeleton))

        experiment = Experiment(modified_description, search_space)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        return experiment, search_space
