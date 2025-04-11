from typing import Dict, Tuple
from copy import deepcopy

from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from core_entities.search_space import SearchSpace
from configuration_selection.configuration_selection import ConfigurationSelection
from transfer_learning.transfer_learning_module import TransferLearningOrchestrator
from tools.initial_config import load_experiment_setup
from tools.restore_db import RestoreDB


experiment_description_file = "./Resources/tests/test_cases_product_configurations/test_case_0.json"
rdb = RestoreDB()


class TestMTL:
    def test_0(self, get_workers, get_configurations_2_float):
        """
        only best
        """
        rdb.restore()
        experiment, search_space = self.initialize_exeriment()
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

        transferred_configs = tl.transfer_submodules["Configuration_transfer"].transfer_configurations(similar_experiments)
        assert len(transferred_configs) > 0

    def test_1(self, get_workers, get_configurations_2_float):
        """
        Few shot
        """
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
                "MultiTaskLearning": {
                    "Filters": {
                        "FewShotMultiTask": {
                            "Type": "few_shot"
                        }
                    }
                }
            }
        }
        experiment, search_space = self.initialize_exeriment(few_shot_skeleton)
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

        transferred_configs = tl.transfer_submodules["Configuration_transfer"].transfer_configurations(similar_experiments)
        assert len(transferred_configs) == 1

    def test_2(self, get_workers, get_configurations_2_float):
        """
        Shuffle
        """

        shuffle_skeleton = {
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
                "MultiTaskLearning": {
                    "Filters": {
                        "ShuffleConfigurations": {
                            "Type": "shuffle"
                        }
                    }
                }
            }
        }
        experiment, search_space = self.initialize_exeriment(shuffle_skeleton)

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

        transferred_configs = tl.transfer_submodules["Configuration_transfer"].transfer_configurations(similar_experiments)
        assert len(transferred_configs) == len(similar_experiments[0]["Samples"])

    def test_3(self, get_workers, get_configurations_2_float):
        """
        all
        """

        shuffle_skeleton = {
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
                "MultiTaskLearning": {
                    "Filters": {
                        "OldNewRatio": {
                            "OldNewConfigsRatio": 0.1,
                            "Type": "old_new_ratio"
                        },
                        "ShuffleConfigurations": {
                            "Type": "shuffle"
                        },
                        "OnlyBestConfigurations": {
                            "Type": "only_best"
                        },
                        "FewShotMultiTask": {
                            "Type": "few_shot"
                        }
                    }
                }
            }
        }
        experiment, search_space = self.initialize_exeriment(shuffle_skeleton)

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

        transferred_configs = tl.transfer_submodules["Configuration_transfer"].transfer_configurations(similar_experiments)
        assert len(transferred_configs) == 1


    def initialize_exeriment(self, skeleton: Dict = None) -> Tuple[Experiment, SearchSpace]:
        experiment_description, search_space = load_experiment_setup(experiment_description_file)

        modified_description = experiment_description
        if skeleton is not None:
            modified_description = deepcopy(experiment_description)
            modified_description.update(deepcopy(skeleton))

        experiment = Experiment(modified_description, search_space)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        return experiment, search_space
