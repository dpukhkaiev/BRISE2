import pytest
import time

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
        cs = ConfigurationSelection(experiment)
        return ReconfigurationModule(experiment, cs)

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
        cs = reconf_module.configuration_selection

        # Assert first item is what the intial config definied
        assert len(cs.predictor.mapping_region_sampling_strategy) == 1
        assert isinstance(cs.predictor.mapping_region_sampling_strategy.popitem()[1], SobolSequence)

        reconf_module.change_variant("SamplingStrategy", {"MersenneTwister": {"Seed": 1, "Type": "mersenne_twister"}})
        reconf_module.done().reconfigure()

        # Assert the sampling strategy changed
        assert len(cs.predictor.mapping_region_sampling_strategy) == 1
        assert isinstance(cs.predictor.mapping_region_sampling_strategy.popitem()[1], MersenneTwister)

    def test_change_optimizer(self, reconf_module:ReconfigurationModule):
        """Test that the reconfiguration changes the optimizer"""
        cs = reconf_module.configuration_selection

        assert len(cs.predictor.mapping_region_model) == 1
        model = cs.predictor.mapping_region_model.popitem()[1]

        # Assert config was loaded correctly
        assert len(model.mapping_optimizer_objective) == 1
        assert isinstance(model.mapping_optimizer_objective.popitem()[0], MOEA)

        # Change
        sampling_size = 96
        reconf_module.change_variant("Optimizer", {"Instance": { "RandomSearch": {
            "SamplingSize": sampling_size,
            "MultiObjective": False,
            "Type": "random_search"
        }}})
        reconf_module.done().reconfigure()

        # Assert change was successful
        assert len(model.mapping_optimizer_objective) == 1
        optimizer = model.mapping_optimizer_objective.popitem()[0]
        assert isinstance(optimizer, RandomSearch)
        assert optimizer.sampling_size == sampling_size

    def test_change_validator(self, reconf_module:ReconfigurationModule):
        cs = reconf_module.configuration_selection

        assert len(cs.predictor.mapping_region_model) == 1
        model = cs.predictor.mapping_region_model.popitem()[1]

        # Assert config was loaded correctly
        assert model.internal_validator is None
        assert isinstance(model.external_validator, MockValidator)

        # Change
        reconf_module.change_variant("Validator", {"ExternalValidator": {
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
                }})
        reconf_module.done().reconfigure()

        # Assert change was successful
        assert isinstance(model.internal_validator, QualityValidator)
        assert isinstance(model.external_validator, QualityValidator)

    def test_change_candidate_selector(self, reconf_module:ReconfigurationModule):
        cs = reconf_module.configuration_selection

        assert len(cs.predictor.mapping_region_model) == 1
        model = cs.predictor.mapping_region_model.popitem()[1]

        # Assert config was loaded correctly
        assert isinstance(model.candidate_selector, BestMultiPoint)

        # Change
        point_amount = 3
        reconf_module.change_variant("CandidateSelector", {"RandomMultiPointProposal": {
                        "NumberOfPoints": point_amount,
                        "Type": "random_multi_point"
                    }})
        reconf_module.done().reconfigure()

        # Assert change was successful
        assert isinstance(model.candidate_selector, RandomMultiPoint)
        assert model.candidate_selector.number_of_points == point_amount

    def test_change_surrogate(self, reconf_module:ReconfigurationModule):
        cs = reconf_module.configuration_selection

        assert len(cs.predictor.mapping_region_model) == 1
        model = cs.predictor.mapping_region_model.popitem()[1]

        # Assert config was loaded correctly
        assert isinstance(model.mapping_surrogate_objective.popitem()[0], TreeParzenEstimator)

        # Change
        reconf_module.change_variant("Surrogate", {"Instance": {
                        "LinearRegression": {
                            "MultiObjective": False,
                            "Type": "sklearn_model_wrapper",
                            "Class": "sklearn.linear_model.LinearRegression"
                        }
                    }})
        reconf_module.done().reconfigure()
        
        # Assert change was successful
        surrogate = model.mapping_surrogate_objective.popitem()[0]
        assert isinstance(surrogate, SklearnWrapper)
        assert surrogate.feature_name == "LinearRegression"

    def test_change_predictor(self, reconf_module:ReconfigurationModule):
        cs = reconf_module.configuration_selection

        old_predictor = cs.predictor
        assert len(cs.predictor.mapping_region_model) == 1

        # Change
        window_size = 0.5
        reconf_module.change_variant("Predictor", {"WindowSize": window_size,
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
        })
        reconf_module.done().reconfigure()

        # Assert change was successful
        assert len(cs.predictor.mapping_region_model) == 1
        model = cs.predictor.mapping_region_model.popitem()[1]

        assert isinstance(model.candidate_selector, RandomMultiPoint)
        assert cs.predictor.window_size == window_size
        assert old_predictor != cs.predictor

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
        reconf_module.change_variant("StopCondition", {"Instance": {
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
                    }})
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
        reconf_module.change_variant("RepetitionManager", {"MaxFailedTasksPerConfiguration": 1,
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
                }})
        reconf_module.done().reconfigure()

        # Assert change was successful
        repeater = rep_manager.get_repeater(False)
        assert isinstance(repeater, AcceptableErrorBasedType)
        assert repeater.min_tasks_per_configuration == min_tasks
        assert repeater.max_tasks_per_configuration == max_tasks

    def test_change_transfer_learning(self, reconf_module:ReconfigurationModule):
        cs = reconf_module.configuration_selection
        experiment = reconf_module.experiment

        # Assert config was loaded correctly
        assert cs.transfer_is_enabled == True
        assert cs.transfer_learning_orchestrator is not None
        assert cs.transfer_learning_orchestrator.experiment_description == experiment.description

        # Change 1
        min_number_samples = 20
        reconf_module.change_variant("TransferLearning", {"TransferExpediencyDetermination": {
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
        }})
        reconf_module.done().reconfigure()

        # Assert change was successful
        conf_trans = cs.transfer_learning_orchestrator.transfer_submodules["Configuration_transfer"]
        model_trans = cs.transfer_learning_orchestrator.transfer_submodules["Model_transfer"]

        assert cs.transfer_is_enabled == True
        assert isinstance(conf_trans, FewShotDecorator)
        assert model_trans is None

        assert isinstance(cs.transfer_learning_orchestrator.ted_module, SamplingLandmarkBased)
        assert cs.transfer_learning_orchestrator.ted_module.min_number_of_samples == min_number_samples

        # Change 2
        reconf_module.change_variant("TransferLearning", {})
        reconf_module.done().reconfigure()

        # Assert change was successful
        assert cs.transfer_is_enabled == False
        assert cs.transfer_learning_orchestrator is None

    def test_change_single_model(self, get_experiment):
        """Test to change a single model"""
        reconf_module = self._get_reconf_module(get_experiment, experiment_num=8)
        cs = reconf_module.configuration_selection
        
        assert len(cs.predictor.mapping_region_model) == 3

        # Model 0 has best multi point as candidate selector other model has random
        assert any([isinstance(model.candidate_selector, BestMultiPoint) for model in cs.predictor.mapping_region_model.values()])
        assert any([isinstance(model.candidate_selector, RandomMultiPoint) for model in cs.predictor.mapping_region_model.values()])

        # Change Model 1
        reconf_module.change_variant("Model_1", {
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
        })
        reconf_module.done().reconfigure()
        #print([e.vp + " " + str(e.identifiers) for e in Effector.get_all()])

        # Assert that the change worked
        assert len(cs.predictor.mapping_region_model) == 3
        assert all([isinstance(model.candidate_selector, BestMultiPoint) for model in cs.predictor.mapping_region_model.values()])

    def test_change_single_optimizer(self, get_experiment):
        """Test to change a single optimizer"""
        reconf_module = self._get_reconf_module(get_experiment, experiment_num=3)
        cs = reconf_module.configuration_selection

        # Assert that config was loaded correctly
        assert len(cs.predictor.mapping_region_model) == 1

        model = cs.predictor.mapping_region_model.popitem()[1]
        assert len(model.mapping_optimizer_objective) == 5
        
        assert all([isinstance(optimizer, MOEA) for optimizer in list(model.mapping_optimizer_objective.keys())])
        
        # Change
        reconf_module.change_variant("Optimizer_0", {"Instance": {
                        "RandomSearch": {
                            "SamplingSize": 500,
                            "MultiObjective": True,
                            "Type": "random_search"
                        }
                    }})
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
        desc = reconf_module._new_experiment_description["ConfigurationSelection"]["Predictor"]["Model"]
        assert "RandomSearch" in desc["Optimizer_0"]["Instance"] # Single changed optimizer

        for i in range(1, 5):
            assert "MOEA" in desc["Optimizer_" + str(i)]["Instance"] # Others are untouched

    def test_change_single_surrogate_on_multiple_models(self, get_experiment):
        """Test to change a single surrogate on a experiment with multiple models"""
        reconf_module = self._get_reconf_module(get_experiment, experiment_num=8)
        cs = reconf_module.configuration_selection

        # Assert that config was loaded correctly
        assert len(cs.predictor.mapping_region_model) == 3

        model_ones = [model for model in cs.predictor.mapping_region_model.values() if model.model_name == "Model_1"]
        assert len(model_ones) == 2

        surrogate_types = ["LinearRegression", "GradientBoostingRegressor", "BayesianRidgeRegression", "ModelMock"]
        for model in model_ones:
            for s in list(model.mapping_surrogate_objective.keys()):
                assert s.feature_name in surrogate_types
        
        # Change
        reconf_module.change_variant("Surrogate_0", {"Instance": {
                        "ModelMock": {
                            "MultiObjective": True,
                            "Type": "model_mock"
                        }
                    }}, ["Model_1"])
        reconf_module.done().reconfigure()
        
        # Assert that change was correct
        surrogate_types = ["GradientBoostingRegressor", "BayesianRidgeRegression", "ModelMock"] # No LinearRegression any more
        for model in model_ones:
            for s in list(model.mapping_surrogate_objective.keys()):
                assert s.feature_name in surrogate_types

        # Assert that model was changed correctly
        desc = reconf_module._new_experiment_description["ConfigurationSelection"]["Predictor"]
        org_desc = reconf_module.experiment.description["ConfigurationSelection"]["Predictor"]

        assert desc["Model_0"] == org_desc["Model_0"] # Model 0 stays the same

        assert "ModelMock" in desc["Model_1"]["Surrogate_0"]["Instance"] # Changed
        assert "GradientBoostingRegressor" in desc["Model_1"]["Surrogate_1"]["Instance"] # Unchanged
        assert "BayesianRidgeRegression" in desc["Model_1"]["Surrogate_2"]["Instance"] # Unchanged
        assert "ModelMock" in desc["Model_1"]["Surrogate_3"]["Instance"] # Unchanged

    def test_change_component_on_multiple_models(self, get_experiment):
        reconf_module = self._get_reconf_module(get_experiment, experiment_num=12)
        cs = reconf_module.configuration_selection
        
        assert len(cs.predictor.mapping_region_model) == 3
        assert all([isinstance(model.candidate_selector, BestMultiPoint) for model in cs.predictor.mapping_region_model.values()])

        # Case 1: Change of all models
        reconf_module.change_variant("CandidateSelector", {"RandomMultiPointProposal": {
                        "NumberOfPoints": 1,
                        "Type": "random_multi_point"
                    }})
        reconf_module.done().reconfigure()

        assert all([isinstance(model.candidate_selector, RandomMultiPoint) for model in cs.predictor.mapping_region_model.values()])

        # Assert that the internal model is correct
        desc = reconf_module._new_experiment_description["ConfigurationSelection"]["Predictor"]
        assert "RandomMultiPointProposal" in desc["Model_0"]["CandidateSelector"]
        assert "RandomMultiPointProposal" in desc["Model_1"]["CandidateSelector"]

        # Case 2: Change of one model
        reconf_module.change_variant("CandidateSelector", {"BestMultiPointProposal": {
                        "NumberOfPoints": 1,
                        "Type": "best_multi_point"
                    }}, ["Model_1"])
        reconf_module.done().reconfigure()

        assert any([isinstance(model.candidate_selector, BestMultiPoint) for model in cs.predictor.mapping_region_model.values()])
        assert any([isinstance(model.candidate_selector, RandomMultiPoint) for model in cs.predictor.mapping_region_model.values()])

        # Assert that the internla model is correct
        assert "RandomMultiPointProposal" in desc["Model_0"]["CandidateSelector"] # Model 0 must be remain unchanged
        assert "BestMultiPointProposal" in desc["Model_1"]["CandidateSelector"]