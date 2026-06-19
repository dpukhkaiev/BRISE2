import pytest
import time
import json
import copy

from core_entities.experiment import Experiment
from configuration_selection.configuration_selection import ConfigurationSelection
from configuration_selection.sampling.mersenne_twister import MersenneTwister
from configuration_selection.sampling.sobol_sequence import SobolSequence
from configuration_selection.model.optimizer.moea import MOEA
from configuration_selection.model.optimizer.random_search import RandomSearch
from configuration_selection.model.validator.mock_validator import MockValidator
from configuration_selection.model.validator.quality_validator import QualityValidator
from configuration_selection.model.candidate_selector.best_multi_point import BestMultiPoint
from configuration_selection.model.candidate_selector.random_multi_point import RandomMultiPoint
from configuration_selection.model.surrogate.tree_parzen_estimator import TreeParzenEstimator
from configuration_selection.model.surrogate.sklearn_wrapper import SklearnWrapper
from stop_condition.stop_condition_selector import StopConditionSelector
from stop_condition.bad_configuration_based import BadConfigurationBasedType
from stop_condition.time_based import TimeBased
from repeater.repeater_selector import RepeaterOrchestration
from repeater.quantity_based import QuantityBasedType
from repeater.acceptable_error_based import AcceptableErrorBasedType
from transfer_learning.multi_task_learning.few_shot import FewShotDecorator
from transfer_learning.transfer_expediency_determination.sampling_landmark_based import SamplingLandmarkBased

from reconfiguration.reconfiguration_module import ReconfigurationModule, RECONFIGURATION_TIMEOUT
from reconfiguration.effector import Effector

class TestReconfigurationModule:

    @pytest.fixture(scope='function')
    def reconf_module(self, get_experiment):
        return self._get_reconf_module(get_experiment)
    
    @pytest.fixture(scope='function')
    def reconf_module_multi_models(self, get_experiment):
        return self._get_reconf_module(get_experiment, experiment_num=8)
    
    def _get_reconf_module(self, get_experiment, experiment_num:int = 0):
        """Make a separate function out of it to reuse it for diffrent experiment numbers"""
        Effector.clear_all()

        experiment_description, search_space = get_experiment(experiment_num)
        experiment = Experiment(experiment_description, search_space)
        return ReconfigurationModule(experiment)

    #@pytest.mark.skip(reason="Takes to much time now. Unskip later")
    def test_unfinished_configuration(self, reconf_module:ReconfigurationModule):
        """Test that unfinished configurations are skipped by the check_for_reconfiguration() method.
        Also checks that the timeout is performed correctly."""
        reconf_module.change_variant("SamplingStrategy", {})

        # Check info methods
        assert reconf_module.finished_configuration() == False
        assert reconf_module.unfinished_configuration() == True

        # Check check method and timeout
        start_time = time.time()
        assert reconf_module.check_for_reconfiguration() == False
        waiting_time = time.time() - start_time
        assert waiting_time >= RECONFIGURATION_TIMEOUT, "Timeout does not work"

    def test_invalid_change_variant(self, reconf_module:ReconfigurationModule):
        """Test that unknwon variability points raise a ValueError"""
        with pytest.raises(ValueError):
            reconf_module.change_variant("UnkownVP", {})

    def test_invalid_done_usage(self, reconf_module:ReconfigurationModule):
        """Test that the done() method can not be called before a change was requested"""
        with pytest.raises(AssertionError):
            reconf_module.done()

    def test_invalid_reconfigure_usage(self, reconf_module:ReconfigurationModule):
        """Test that the reconfigure() method can not be called before the configuration was marked as done"""
        # Case 1: No configuration requested
        with pytest.raises(AssertionError):
            reconf_module.reconfigure()

        # Case 2: Unfinished configuration
        reconf_module.change_variant("SamplingStrategy", {})

        with pytest.raises(AssertionError):
            reconf_module.reconfigure()

    def test_change_sampling_strategy(self, reconf_module:ReconfigurationModule):
        """Test that the reconfiguration changes the sampling strategy"""
        cs = ConfigurationSelection(reconf_module.experiment)

        # Assert first item is what the intial config definied
        assert len(cs.predictor.mapping_region_sampling_strategy) == 1
        assert isinstance(cs.predictor.mapping_region_sampling_strategy.popitem()[1], SobolSequence)

        desc = {"MersenneTwister": {"Seed": 1, "Type": "mersenne_twister"}}
        reconf_module.change_variant("SamplingStrategy", desc)
        reconf_module.done().reconfigure()

        # Assert the sampling strategy changed
        assert len(cs.predictor.mapping_region_sampling_strategy) == 1
        assert isinstance(cs.predictor.mapping_region_sampling_strategy.popitem()[1], MersenneTwister)

        # Assert that model was changed correctly
        expected_desc = copy.deepcopy(reconf_module.experiment.description)
        expected_desc["ConfigurationSelection"]["SamplingStrategy"] = desc
        assert reconf_module._new_experiment_description == expected_desc

    def test_change_optimizer(self, reconf_module:ReconfigurationModule):
        """Test that the reconfiguration changes the optimizer"""
        cs = ConfigurationSelection(reconf_module.experiment)

        assert len(cs.predictor.mapping_region_model) == 1
        model = cs.predictor.mapping_region_model.popitem()[1]

        # Assert config was loaded correctly
        assert len(model.mapping_optimizer_objective) == 1
        assert isinstance(model.mapping_optimizer_objective.popitem()[0], MOEA)

        # Change
        desc = {"Instance": { "RandomSearch": {
            "SamplingSize": 96,
            "MultiObjective": False,
            "Type": "random_search"
        }}}
        reconf_module.change_variant("Optimizer", desc)
        reconf_module.done().reconfigure()

        # Assert change was successful
        assert len(model.mapping_optimizer_objective) == 1
        optimizer = model.mapping_optimizer_objective.popitem()[0]
        assert isinstance(optimizer, RandomSearch)
        assert optimizer.sampling_size == desc["Instance"]["RandomSearch"]["SamplingSize"]

        # Assert that model was changed correctly
        expected_desc = copy.deepcopy(reconf_module.experiment.description)
        expected_desc["ConfigurationSelection"]["Predictor"]["Model"]["Optimizer"] = desc
        assert reconf_module._new_experiment_description == expected_desc

    def test_change_validator(self, reconf_module:ReconfigurationModule):
        cs = ConfigurationSelection(reconf_module.experiment)

        assert len(cs.predictor.mapping_region_model) == 1
        model = cs.predictor.mapping_region_model.popitem()[1]

        # Assert config was loaded correctly
        assert model.internal_validator is None
        assert isinstance(model.external_validator, MockValidator)

        # Change
        desc = {"ExternalValidator": {
                    "QualityValidator": {
                        "Split": {
                            "HoldOut": {
                                "TrainingSet": 0.9
                            }
                        },
                        "QualityThreshold": 0.3,
                        "Type": "quality_validator"
                    }
                },
                "InternalValidator": {
                    "QualityValidator": {
                        "Split": {
                            "KFold": {
                                "NumberOfFolds": 4
                            }
                        },
                        "QualityThreshold": 0.65,
                        "Type": "quality_validator"
                    }
                }}
        reconf_module.change_variant("Validator", desc)
        reconf_module.done().reconfigure()

        # Assert change was successful
        assert isinstance(model.internal_validator, QualityValidator)
        assert isinstance(model.external_validator, QualityValidator)

        # Assert that model was changed correctly
        expected_desc = copy.deepcopy(reconf_module.experiment.description)
        expected_desc["ConfigurationSelection"]["Predictor"]["Model"]["Validator"] = desc
        assert reconf_module._new_experiment_description == expected_desc

    def test_change_candidate_selector(self, reconf_module:ReconfigurationModule):
        cs = ConfigurationSelection(reconf_module.experiment)

        assert len(cs.predictor.mapping_region_model) == 1
        model = cs.predictor.mapping_region_model.popitem()[1]

        # Assert config was loaded correctly
        assert isinstance(model.candidate_selector, BestMultiPoint)

        # Change
        number_of_points = 3
        desc = {"RandomMultiPointProposal": {
                        "NumberOfPoints": number_of_points,
                        "Type": "random_multi_point"
                    }}
        reconf_module.change_variant("CandidateSelector", desc)
        reconf_module.done().reconfigure()

        # Assert change was successful
        assert isinstance(model.candidate_selector, RandomMultiPoint)
        assert model.candidate_selector.number_of_points == number_of_points

        # Assert that model was changed correctly
        expected_desc = copy.deepcopy(reconf_module.experiment.description)
        expected_desc["ConfigurationSelection"]["Predictor"]["Model"]["CandidateSelector"] = desc
        assert reconf_module._new_experiment_description == expected_desc

    def test_change_surrogate(self, reconf_module:ReconfigurationModule):
        cs = ConfigurationSelection(reconf_module.experiment)

        assert len(cs.predictor.mapping_region_model) == 1
        model = cs.predictor.mapping_region_model.popitem()[1]

        # Assert config was loaded correctly
        assert isinstance(model.mapping_surrogate_objective.popitem()[0], TreeParzenEstimator)

        # Change
        desc = {"Instance": {
                        "LinearRegression": {
                            "MultiObjective": False,
                            "Type": "sklearn_model_wrapper",
                            "Class": "sklearn.linear_model.LinearRegression"
                        }
                    }}
        reconf_module.change_variant("Surrogate", desc)
        reconf_module.done().reconfigure()
        
        # Assert change was successful
        surrogate = model.mapping_surrogate_objective.popitem()[0]
        assert isinstance(surrogate, SklearnWrapper)
        assert surrogate.feature_name == "LinearRegression"

        # Assert that model was changed correctly
        expected_desc = copy.deepcopy(reconf_module.experiment.description)
        expected_desc["ConfigurationSelection"]["Predictor"]["Model"]["Surrogate"] = desc
        assert reconf_module._new_experiment_description == expected_desc

    def test_change_predictor(self, reconf_module:ReconfigurationModule):
        cs = ConfigurationSelection(reconf_module.experiment)

        old_predictor = cs.predictor
        assert len(cs.predictor.mapping_region_model) == 1

        # Change
        window_size = 0.5
        desc = {"WindowSize": window_size,
            "Model": {
                "Surrogate": {
                    "ConfigurationTransformers": {
                        "FloatTransformer": {
                            "SklearnFloatMinMaxScaler": {
                                "Type": "sklearn_float_transformer",
                                "Class": "sklearn.MinMaxScaler"
                            }
                        }
                    },
                    "Instance": {
                        "TreeParzenEstimator": {
                            "MultiObjective": False,
                            "Parameters": {
                                "top_n_percent": 30,
                                "random_fraction": 0.1,
                                "bandwidth_factor": 3.0,
                                "min_bandwidth": 0.001
                            },
                            "Type": "tree_parzen_estimator"
                        }
                    }
                },
                "Optimizer": {
                    "ConfigurationTransformers": {
                        "FloatTransformer": {
                            "SklearnFloatMinMaxScaler": {
                                "Type": "sklearn_float_transformer",
                                "Class": "sklearn.MinMaxScaler"
                            }
                        }
                    },
                    "ValueTransformers": {
                        "AcquisitionFunction": {
                            "TPE_EI": {
                                "Type": "tpe_ei"
                            }
                        }
                    },
                    "Instance": {
                        "MOEA": {
                            "Generations": 10,
                            "PopulationSize": 100,
                            "Algorithms": {
                                "GACO": {
                                    "MultiObjective": False
                                }
                            },
                            "Type": "moea"
                        }
                    }
                },
                "Validator": {
                    "ExternalValidator": {
                        "MockValidator": {
                            "Type": "mock_validator"
                        }
                    }
                },
                "CandidateSelector": {
                    "RandomMultiPointProposal": {
                        "NumberOfPoints": 1,
                        "Type": "random_multi_point"
                    }
                }
            }
        }
        reconf_module.change_variant("Predictor", desc)
        reconf_module.done().reconfigure()

        # Assert change was successful
        assert len(cs.predictor.mapping_region_model) == 1
        model = cs.predictor.mapping_region_model.popitem()[1]

        assert isinstance(model.candidate_selector, RandomMultiPoint)
        assert cs.predictor.window_size == window_size
        assert old_predictor != cs.predictor

        # Assert that model was changed correctly
        expected_desc = copy.deepcopy(reconf_module.experiment.description)
        expected_desc["ConfigurationSelection"]["Predictor"] = desc
        assert reconf_module._new_experiment_description == expected_desc

    def test_change_stop_condition(self, reconf_module:ReconfigurationModule):
        """Test that stop condition are changed"""
        experiment = reconf_module.experiment

        sc_selector = StopConditionSelector()
        old_scs = sc_selector.launch_stop_condition_threads(experiment.unique_id, experiment)
        old_sc_validator = sc_selector.stop_condition_validator

        # Add StopCondition point
        reconf_module.executor.update_effectors(do_cleanup=False) # Set to False to prevent to cleanup "StopCondition" VP

        assert len(old_scs) == 1
        assert isinstance(old_scs[0], BadConfigurationBasedType)

        # Change
        max_run_time_in_s = 10
        desc = {"Instance": {
                        "TimeBasedSC": {
                            "Parameters": {
                                "MaxRunTime": max_run_time_in_s,
                                "TimeUnit": "seconds"
                            },
                            "Type": "time_based",
                            "Name": "t"
                        }
                    },
                    "StopConditionTriggerLogic": {
                        "Expression": "t",
                        "InspectionParameters": {
                            "RepetitionPeriod": 1,
                            "TimeUnit": "seconds"
                        }
                    }}
        reconf_module.change_variant("StopCondition", desc)
        reconf_module.done().reconfigure()

        # Assert change was successful
        assert len(sc_selector.stop_conditions) == 1
        assert isinstance(sc_selector.stop_conditions[0], TimeBased)
        assert sc_selector.stop_conditions[0].interval == max_run_time_in_s

        assert sc_selector.stop_condition_validator != old_sc_validator
        assert sc_selector.stop_condition_validator.expression == "t"

        # Assert old threads are stopped
        assert old_sc_validator.active == False

        for sc in old_scs:
            assert sc.active == False

        # Assert that model was changed correctly
        expected_desc = copy.deepcopy(reconf_module.experiment.description)
        expected_desc["StopCondition"] = desc
        assert reconf_module._new_experiment_description == expected_desc

    def test_change_repetition_manager(self, reconf_module:ReconfigurationModule):
        experiment = reconf_module.experiment

        rep_manager = RepeaterOrchestration(experiment_id=experiment.unique_id, experiment=experiment)

        # Add varibility point
        reconf_module.executor.update_effectors(do_cleanup=False)

        # Assert config was loaded correctly
        repeater = rep_manager.get_repeater(False)
        assert isinstance(repeater, QuantityBasedType)
        assert repeater.max_tasks_per_configuration == 10
        
        # Change
        max_tasks = 7
        min_tasks = 2
        desc = {"MaxFailedTasksPerConfiguration": 1,
                "Instance": {
                    "AcceptableErrorBased": {
                        "MinTasksPerConfiguration": min_tasks,
                        "MaxTasksPerConfiguration": max_tasks,
                        "BaseAcceptableError": 3.0,
                        "ConfidenceLevel": 0.95,
                        "Type": "acceptable_error_based",
                        "ExperimentAware": {
                            "MaxAcceptableError": 50.0,
                            "RatioMax": 3.0,
                            "MinTasksPerUnderperformingConfiguration": 1
                        }
                    }
                }}
        reconf_module.change_variant("RepetitionManager", desc)
        reconf_module.done().reconfigure()

        # Assert change was successful
        repeater = rep_manager.get_repeater(False)
        assert isinstance(repeater, AcceptableErrorBasedType)
        assert repeater.min_tasks_per_configuration == min_tasks
        assert repeater.max_tasks_per_configuration == max_tasks

        # Assert that model was changed correctly
        expected_desc = copy.deepcopy(reconf_module.experiment.description)
        expected_desc["RepetitionManager"] = desc
        assert reconf_module._new_experiment_description == expected_desc

    def test_change_transfer_learning(self, reconf_module:ReconfigurationModule):
        cs = ConfigurationSelection(reconf_module.experiment)
        experiment = reconf_module.experiment

        # Assert config was loaded correctly
        assert cs.transfer_is_enabled == True
        assert cs.transfer_learning_orchestrator is not None
        assert cs.transfer_learning_orchestrator.experiment_description == experiment.description

        # Change 1
        min_number_samples = 20
        desc = {"TransferExpediencyDetermination": {
            "SamplingLandmarkBased": {
                "MinNumberOfSamples": min_number_samples,
                "Type": "sampling_landmark_based",
                "Comparator": {
                    "NormDifference": {
                        "Type": "norm_difference_comparator"
                    }
                },
                "ExperimentsQuantity": {
                    "FixedQuantity": {
                        "NumberOfSimilarExperiments": 5
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
        }}
        reconf_module.change_variant("TransferLearning", desc)
        reconf_module.done().reconfigure()

        # Assert change was successful
        conf_trans = cs.transfer_learning_orchestrator.transfer_submodules["Configuration_transfer"]
        model_trans = cs.transfer_learning_orchestrator.transfer_submodules["Model_transfer"]

        assert cs.transfer_is_enabled == True
        assert isinstance(conf_trans, FewShotDecorator)
        assert model_trans is None

        assert isinstance(cs.transfer_learning_orchestrator.ted_module, SamplingLandmarkBased)
        assert cs.transfer_learning_orchestrator.ted_module.min_number_of_samples == min_number_samples

        # Assert that model was changed correctly
        expected_desc = copy.deepcopy(reconf_module.experiment.description)
        expected_desc["TransferLearning"] = desc
        assert reconf_module._new_experiment_description == expected_desc

        # Change 2
        reconf_module.change_variant("TransferLearning", {})
        reconf_module.done().reconfigure()

        # Assert change was successful
        assert cs.transfer_is_enabled == False
        assert cs.transfer_learning_orchestrator is None

    def test_change_single_model(self, get_experiment):
        """Test to change a single model"""
        reconf_module = self._get_reconf_module(get_experiment, experiment_num=8)
        cs = ConfigurationSelection(reconf_module.experiment)
        
        assert len(cs.predictor.mapping_region_model) == 3

        # Model 0 has best multi point as candidate selector other model has random
        assert any([isinstance(model.candidate_selector, BestMultiPoint) for model in cs.predictor.mapping_region_model.values()])
        assert any([isinstance(model.candidate_selector, RandomMultiPoint) for model in cs.predictor.mapping_region_model.values()])

        # Change Model 1
        desc = {
            "MultiObjectiveHandling": {
                    "SurrogateType": {
                        "Scalar": {}
                    }
                },
                "Surrogate": {
                    "ValueTransformers": {
                        "ValueScalarizator": {
                            "WeightedSum": {
                                "Weights": [1, 2],
                                "Type": "weighted_sum"
                            }
                        }
                    },
                    "Instance": {
                        "MultiArmedBandit": {
                            "MultiObjective": False,
                            "CType": "std",
                            "CFloat": 1.0,
                            "Parameters": {
                                "c": "std"
                            },
                            "Type": "multi_armed_bandit"
                        }
                    }
                },
                "Optimizer": {
                    "Instance": {
                        "RandomSearch": {
                            "SamplingSize": 500,
                            "MultiObjective": True,
                            "Type": "random_search"
                        }
                    }
                },
                "Validator": {
                    "ExternalValidator": {
                        "MockValidator": {
                            "Type": "mock_validator"
                        }
                    }
                },
                "CandidateSelector": {
                    "BestMultiPointProposal": {
                        "NumberOfPoints": 1,
                        "Type": "best_multi_point"
                    }
                }
        }
        reconf_module.change_variant("Model_1", desc)
        reconf_module.done().reconfigure()
        #print([e.vp + " " + str(e.identifiers) for e in Effector.get_all()])

        # Assert that the change worked
        assert len(cs.predictor.mapping_region_model) == 3
        assert all([isinstance(model.candidate_selector, BestMultiPoint) for model in cs.predictor.mapping_region_model.values()])

        # Assert that model was changed correctly
        expected_desc = copy.deepcopy(reconf_module.experiment.description)
        expected_desc["ConfigurationSelection"]["Predictor"]["Model_1"] = desc
        assert reconf_module._new_experiment_description == expected_desc

    def test_change_single_optimizer(self, get_experiment):
        """Test to change a single optimizer"""
        reconf_module = self._get_reconf_module(get_experiment, experiment_num=3)
        cs = ConfigurationSelection(reconf_module.experiment)

        # Assert that config was loaded correctly
        assert len(cs.predictor.mapping_region_model) == 1
        
        model = cs.predictor.mapping_region_model.popitem()[1]
        assert len(model.mapping_optimizer_objective) == 5
        
        assert all([isinstance(optimizer, MOEA) for optimizer in list(model.mapping_optimizer_objective.keys())])
        
        # Change
        optimizer_desc = {"Instance": {
                        "RandomSearch": {
                            "SamplingSize": 500,
                            "MultiObjective": True,
                            "Type": "random_search"
                        }
                    }}
        reconf_module.change_variant("Optimizer_0", optimizer_desc)
        reconf_module.done().reconfigure()

        # Assert that the change worked
        assert len(model.mapping_optimizer_objective) == 5

        moea_count = 0
        random_count = 0
        for optimizer in list(model.mapping_optimizer_objective.keys()):
            if isinstance(optimizer, MOEA):
                moea_count += 1
                continue

            if isinstance(optimizer, RandomSearch):
                random_count += 1

        assert moea_count == 4
        assert random_count == 1

        # Assert that model was changed correctly
        expected_desc = copy.deepcopy(reconf_module.experiment.description)
        expected_desc["ConfigurationSelection"]["Predictor"]["Model"]["Optimizer_0"] = optimizer_desc
        assert reconf_module._new_experiment_description == expected_desc

    def test_change_single_surrogate_on_multiple_models(self, get_experiment):
        """Test to change a single surrogate on a experiment with multiple models"""
        reconf_module = self._get_reconf_module(get_experiment, experiment_num=8)
        cs = ConfigurationSelection(reconf_module.experiment)

        # Assert that config was loaded correctly
        assert len(cs.predictor.mapping_region_model) == 3
        #print([e.vp + " " + str(e.identifiers) for e in Effector.get_all()])
        model_ones = [model for model in cs.predictor.mapping_region_model.values() if model.model_name == "Model_1"]
        assert len(model_ones) == 2

        surrogate_types = ["LinearRegression", "GradientBoostingRegressor", "BayesianRidgeRegression", "ModelMock"]
        for model in model_ones:
            for s in list(model.mapping_surrogate_objective.keys()):
                assert s.feature_name in surrogate_types
        
        # Change
        surrogate_desc = {"Instance": {"ModelMock": {
                            "MultiObjective": True,
                            "Type": "model_mock"
                        }
                    }}
        reconf_module.change_variant("Surrogate_0", surrogate_desc, ["Model_1"])
        reconf_module.done().reconfigure()
        
        # Assert that change was correct
        surrogate_types = ["GradientBoostingRegressor", "BayesianRidgeRegression", "ModelMock"] # No LinearRegression any more
        for model in model_ones:
            for s in list(model.mapping_surrogate_objective.keys()):
                assert s.feature_name in surrogate_types

        # Assert that model was changed correctly
        expected_desc = copy.deepcopy(reconf_module.experiment.description)
        expected_desc["ConfigurationSelection"]["Predictor"]["Model_1"]["Surrogate_0"] = surrogate_desc
        assert reconf_module._new_experiment_description == expected_desc

    def test_change_component_on_multiple_models(self, get_experiment):
        reconf_module = self._get_reconf_module(get_experiment, experiment_num=12)
        cs = ConfigurationSelection(reconf_module.experiment)
        
        assert len(cs.predictor.mapping_region_model) == 3
        assert all([isinstance(model.candidate_selector, BestMultiPoint) for model in cs.predictor.mapping_region_model.values()])

        # Case 1: Change of all models
        candidate_selector_desc_1 = {"RandomMultiPointProposal": {
                        "NumberOfPoints": 1,
                        "Type": "random_multi_point"
                    }}
        reconf_module.change_variant("CandidateSelector", candidate_selector_desc_1)
        reconf_module.done().reconfigure()

        assert all([isinstance(model.candidate_selector, RandomMultiPoint) for model in cs.predictor.mapping_region_model.values()])

        # Assert that the internal model is correct
        expected_desc = copy.deepcopy(reconf_module.experiment.description)
        expected_desc["ConfigurationSelection"]["Predictor"]["Model_0"]["CandidateSelector"] = candidate_selector_desc_1
        expected_desc["ConfigurationSelection"]["Predictor"]["Model_1"]["CandidateSelector"] = candidate_selector_desc_1
        assert reconf_module._new_experiment_description == expected_desc

        # Case 2: Change of one model
        candidate_selector_desc_2 = {"BestMultiPointProposal": {
                        "NumberOfPoints": 1,
                        "Type": "best_multi_point"
                    }}
        reconf_module.change_variant("CandidateSelector", candidate_selector_desc_2, ["Model_1"])
        reconf_module.done().reconfigure()

        assert any([isinstance(model.candidate_selector, BestMultiPoint) for model in cs.predictor.mapping_region_model.values()])
        assert any([isinstance(model.candidate_selector, RandomMultiPoint) for model in cs.predictor.mapping_region_model.values()])

        # Assert that the internal model is correct
        expected_desc["ConfigurationSelection"]["Predictor"]["Model_1"]["CandidateSelector"] = candidate_selector_desc_2
        assert reconf_module._new_experiment_description == expected_desc

    def test_change_values(self, reconf_module:ReconfigurationModule):
        """Test that the `change_variables` method works correctly"""
        cs = ConfigurationSelection(reconf_module.experiment)

        assert cs.predictor.window_size == 1.0

        # Change
        new_size = 0.5
        reconf_module.change_variables("Predictor", {"WindowSize": new_size})
        reconf_module.done().reconfigure()

        # Assert that the change was correct
        assert cs.predictor.window_size == new_size
        assert reconf_module._new_experiment_description["ConfigurationSelection"]["Predictor"]["WindowSize"] == new_size

        # Change via "multiple" wrapper
        new_size = 0.8
        reconf_module.change_multiple_variables([{"vp": "Predictor", "new_values": {"WindowSize": new_size}}])
        reconf_module.done().reconfigure()

        # Assert that the change was correct
        assert cs.predictor.window_size == new_size
        assert reconf_module._new_experiment_description["ConfigurationSelection"]["Predictor"]["WindowSize"] == new_size

    def test_update_surrogate_and_optimizers_with_reconfiguration(self, get_experiment):
        """Test that the update_surrogate_and_optimizers() in model.py works with the reconfiguration"""
        reconf_module = self._get_reconf_module(get_experiment, experiment_num=3)
        cs = ConfigurationSelection(reconf_module.experiment)

        # Assert that config was loaded correctly
        assert len(cs.predictor.mapping_region_model) == 1
        
        model = cs.predictor.mapping_region_model.popitem()[1]
        assert len(model.mapping_optimizer_objective) == 5
        
        assert all([isinstance(optimizer, MOEA) for optimizer in list(model.mapping_optimizer_objective.keys())])

        # Mock change via update_method
        surrogate_desc = {
            "Instance": {
                "TreeParzenEstimator": {
                    "MultiObjective": False,
                    "Parameters": {
                        "top_n_percent": 20,
                        "random_fraction": 0.0,
                        "bandwidth_factor": 1.0,
                        "min_bandwidth": 0.001
                    },
                    "Type": "tree_parzen_estimator"
                }
            }
        }

        optimizer_desc = {"Instance": {
                        "RandomSearch": {
                            "SamplingSize": 500,
                            "MultiObjective": True,
                            "Type": "random_search"
                        }
                    }}

        update_list = [{
            "Surrogate": surrogate_desc,
            "Objectives_surrogate": self.__get_first_elem(model.mapping_surrogate_objective),
            "Optimizer": optimizer_desc,
            "Objectives_optimizer": self.__get_first_elem(model.mapping_optimizer_objective)
        }]
        model.update_surrogates_and_optimizers(update_list)
        
        # Assert the update worked
        assert len(model.mapping_optimizer_objective) == 5

        moea_count = 0
        random_count = 0
        for optimizer in list(model.mapping_optimizer_objective.keys()):
            if isinstance(optimizer, MOEA):
                moea_count += 1
                continue

            if isinstance(optimizer, RandomSearch):
                random_count += 1

        assert moea_count == 4
        assert random_count == 1

        # Reconfigure
        optimizer_desc = {
            "Instance": {
                "MOEA": {
                    "Generations": 5,
                    "PopulationSize": 80,
                    "Algorithms": {
                        "GACO": {
                            "MultiObjective": False
                        }
                    },
                    "Type": "moea"
                }
            }
        }

        reconf_module.change_variant("Optimizer_0", optimizer_desc)
        reconf_module.done().reconfigure()

        # Assert that change was successful
        assert len(model.mapping_optimizer_objective) == 5
        assert all([isinstance(optimizer, MOEA) for optimizer in list(model.mapping_optimizer_objective.keys())])

    def test_cleanup_surrogates_and_optimizers_on_reconf(self, get_experiment):
        """Test that the cleanup process for optimizers and surrogates is working"""
        reconf_module = self._get_reconf_module(get_experiment, experiment_num=5)
        cs = ConfigurationSelection(reconf_module.experiment)

        # Assert that config was loaded correctly
        assert len(cs.predictor.mapping_region_model) == 1
        
        model = self.__get_first_elem(cs.predictor.mapping_region_model)
        assert len(model.mapping_surrogate_objective) == 11
        assert len(model.mapping_optimizer_objective) == 1

        # Assert that internal maps are correctly
        assert len(model._surrogate_map) == 5
        assert len(model._optimizer_map) == 1

        assert list(model._surrogate_map.keys()) == ["Surrogate_" + str(i) for i in range(5)]
        assert list(model._optimizer_map.keys()) == ["Optimizer"]

        old_surrogate_map = copy.copy(model._surrogate_map)
        old_optimizer_map = copy.copy(model._optimizer_map)

        old_optimizer = old_optimizer_map["Optimizer"][0]

        for key, surrogates in model._surrogate_map.items():
            assert len(surrogates) == 3 if key == "Surrogate_0" else 2

        # Change
        surrogate_desc = {
            "Instance": {
                "ModelMock": {
                    "MultiObjective": True,
                    "Type": "model_mock"
                }
            }
        }

        optimizer_desc = {
            "Instance": {
                "RandomSearch": {
                    "SamplingSize": 96,
                    "MultiObjective": False,
                    "Type": "random_search"
                }
            }
        }

        reconf_module.change_variant("Surrogate_1", surrogate_desc)
        reconf_module.change_variant("Optimizer", optimizer_desc)
        reconf_module.done().reconfigure()

        # Assert old surrogates/optimizers were deleted and maps are correct
        assert len(model._optimizer_map) == 1
        assert old_optimizer_map != model._optimizer_map
        assert old_optimizer != model._optimizer_map["Optimizer"][0]
        assert all([o != old_optimizer for o in model.mapping_optimizer_objective.keys()])

        assert len(model._surrogate_map) == 5
        for key, surrogates in model._surrogate_map.items():
            assert len(surrogates) == 3 if key == "Surrogate_0" or key == "Surrogate_1" else 2

            if key == "Surrogate_1":
                assert surrogates != old_surrogate_map[key]
                continue

            assert surrogates == old_surrogate_map[key]
        assert all([s not in old_surrogate_map["Surrogate_1"] for s in model.mapping_surrogate_objective.keys()])

    def test_request_change_method(self, reconf_module:ReconfigurationModule):
        """Test the callback for the queue"""
        # 1) Test the redirect to change_variant
        feature_data = {"RandomMultiPointProposal": {
                        "NumberOfPoints": 10,
                        "Type": "random_multi_point"}
                        }
        event = {
            "type": "variant",
            "data": {
                "vp": "CandidateSelector",
                "new_feature": feature_data
            }
        }
        reconf_module.request_change(None, None, None, json.dumps(event).encode())

        assert "CandidateSelector" in reconf_module._requested_changes
        assert reconf_module._requested_changes["CandidateSelector"]["description"] == feature_data
        assert reconf_module._requested_changes["CandidateSelector"]["identifiers"] is None

        # 2) Test redirection to change_variables
        values = {"WindowSize": 0.9}
        event = {
            "type": "variables",
            "data": {
                "vp": "Predictor",
                "new_values": values
            }
        }
        reconf_module.request_change(None, None, None, json.dumps(event).encode())

        assert "Predictor_Values" in reconf_module._requested_changes
        assert reconf_module._requested_changes["Predictor_Values"]["description"] == values

        # 3) Test invalid event type
        event_invalid = {
            "type": "unknown",
            "data": {}
        }

        with pytest.raises(ValueError):
            reconf_module.request_change(None, None, None, json.dumps(event_invalid).encode())

        # 4) Test change multiple variants/variables
        reconf_module._requested_changes.clear()
        assert len(reconf_module._requested_changes) == 0
        
        event_candidate = {
            "type": "variant",
            "data": {
                "vp": "CandidateSelector",
                "new_feature": feature_data
            }
        }

        event_variables = {
            "type": "variables",
            "data": {
                "vp": "Predictor",
                "new_values": values
            }
        }

        reconf_module.request_change(None, None, None, json.dumps([event_candidate, event_variables]).encode())

        assert "CandidateSelector" in reconf_module._requested_changes
        assert reconf_module._requested_changes["CandidateSelector"]["description"] == feature_data
        assert reconf_module._requested_changes["CandidateSelector"]["identifiers"] is None

        assert "Predictor_Values" in reconf_module._requested_changes
        assert reconf_module._requested_changes["Predictor_Values"]["description"] == values

    def test_change_variants(self, reconf_module:ReconfigurationModule):
        """Test that the change_variants method process data correctly"""
        samp_desc = {"MersenneTwister": {"Seed": 1, "Type": "mersenne_twister"}}
        optimizer_desc = {"Instance": { "RandomSearch": {
            "SamplingSize": 96,
            "MultiObjective": False,
            "Type": "random_search"
        }}}
        reconf_module.change_variants([{"vp": "SamplingStrategy", "new_feature": samp_desc},
                                       {"vp": "Optimizer", "new_feature": optimizer_desc, "parent_nodes": ["Model"]}])

        assert "SamplingStrategy" in reconf_module._requested_changes
        assert reconf_module._requested_changes["SamplingStrategy"]["description"] == samp_desc
        assert reconf_module._requested_changes["SamplingStrategy"]["identifiers"] is None

        assert "Optimizer" in reconf_module._requested_changes
        assert reconf_module._requested_changes["Optimizer"]["description"] == optimizer_desc
        assert reconf_module._requested_changes["Optimizer"]["identifiers"] == ["Model"]


    ## Helper
    def __get_first_elem(self, map):
        if len(map) == 0:
            return None
        
        return map[list(map.keys())[0]]