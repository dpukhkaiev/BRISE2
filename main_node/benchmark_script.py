import os
import json
from copy import deepcopy

from tools.initial_config import load_experiment_setup

class Runner:

    def __init__(self):
        self._base_experiment_description = None
        self._base_search_space = None

        self.error_count = 0
        self.distinct_experiements = 0

    @property
    def base_experiment_description(self):
        return deepcopy(self._base_experiment_description)

    @base_experiment_description.setter
    def base_experiment_description(self, description):
        if not self._base_experiment_description:
            self._base_experiment_description = deepcopy(description)
        else:
            print("Unable to update Experiment Description: Read-only property.")

    def execute_experiment(self, description, number_of_repetitions=1):
        # Write to file
        with open("temp_exp.json", "w", encoding="utf-8") as file:
            file.write(json.dumps(description))

        self.distinct_experiements += 1

        for _ in range(number_of_repetitions):
            code = os.system("python3.12 main.py temp_exp.json")
            print("Experiment finished with code", code)
            if code != 0:
                self.error_count += 1
                exit()

        print("Clean up")
        os.remove("temp_exp.json")

    def save_result(self, experiement_name):
        pass

    def clear_results(self):
        for file in os.listdir("./Results"):
            if os.path.isfile(".Results/" + file):
                print("Remove", file)
                os.remove("./Results/" + file)

        print("Removed all previous results")

    def show_results(self):
        print("Ran experiments:", self.distinct_experiements)
        print("Errors:", self.error_count)
        print("See result folder for further details")

    def run_benchmark(self):
        reconf_sampling_and_candidate = {
                "Reconfiguration": {
                    "AfterXConfigurations_0": {
                        "amount": 5,
                        "performAmount": 1,
                        "vp": "SamplingStrategy",
                        "description": {"Sobol": {"Seed": 1, "Type": "sobol"}}
                    },
                    "AfterXConfigurations_1": {
                        "amount": 10,
                        "performAmount": 1,
                        "vp": "CandidateSelector",
                        "description": {"RandomMultiPointProposal": {"NumberOfPoints": 1, "Type": "random_multi_point"}}
                    }
                }
            }

        reconf_stop_condition = {
            "Reconfiguration": {
                "AfterXConfigurations": {
                    "amount": 5,
                    "performAmount": 1,
                    "vp": "StopCondition",
                    "description": {"Instance": {
                        "TimeBasedSC": {
                            "Parameters": {
                                    "MaxRunTime": 10,
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
                        }
                    }
                }
            }
        }

        reconf_optimizer = {
            "Reconfiguration": {
                "AfterXConfigurations": {
                    "amount": 5,
                    "performAmount": 1,
                    "vp": "Optimizer",
                    "description": {"Instance": { "RandomSearch": {
                        "SamplingSize": 96,
                        "MultiObjective": False,
                        "Type": "random_search"
                    }}}
                }
            }
        }

        reconf_validator = {
            "Reconfiguration": {
                "AfterXConfigurations": {
                    "amount": 5,
                    "performAmount": 1,
                    "vp": "Validator",
                    "description": {
                        "ExternalValidator": {
                            "QualityValidator": {
                                "Split": {
                                    "HoldOut": {
                                        "TrainingSet": 0.6
                                    }
                                },
                                "QualityThreshold": 0.3,
                                "Type": "quality_validator"
                            }
                        }
                    }
                }
            }
        }

        reconf_surrogate = {
            "Reconfiguration": {
                "AfterXConfigurations": {
                    "amount": 5,
                    "performAmount": 1,
                    "vp": "Surrogate",
                    "description":{
                        "Instance": {
                            "LinearRegression": {
                                "MultiObjective": False,
                                "Type": "sklearn_model_wrapper",
                                "Class": "sklearn.linear_model.LinearRegression"
                            }
                        }
                    }
                }
            }
        }

        reconf_rep_manager = {
            "Reconfiguration": {
                "AfterXConfigurations": {
                    "amount": 5,
                    "performAmount": 1,
                    "vp": "RepetitionManager",
                    "description":{
                        "MaxFailedTasksPerConfiguration": 2,
                        "Instance": {
                            "QuantityBased": {
                                "MaxTasksPerConfiguration": 2,
                                "Type": "quantity_based"
                            }
                        }
                    }
                }
            }
        }

        reconf_transfer_learning = {
            "Reconfiguration": {
                "AfterXConfigurations": {
                    "amount": 2,
                    "performAmount": 1,
                    "vp": "TransferLearning",
                    "description": {}
                }
            }
        }

        reconf_single_optimizer = {
            "Reconfiguration": {
                "AfterXConfigurations": {
                    "amount": 2,
                    "performAmount": 1,
                    "vp": "Optimizer",
                    "identifiers": ["Model_1"],
                    "description": {
                        "Instance": {
                            "RandomSearch": {
                            "SamplingSize": 300,
                            "MultiObjective": True,
                            "Type": "random_search"
                            }
                        }
                    }
                }
            }
        }

        reconf_single_surrogate = {
            "Reconfiguration": {
                "AfterXConfigurations": {
                    "amount": 2,
                    "performAmount": 1,
                    "vp": "Surrogate_0",
                    "identifiers": ["Model_1"],
                    "description": {
                        "Instance": {
                            "ModelMock": {
                                "MultiObjective": True,
                                "Type": "model_mock"
                            }
                        }
                    }
                }
            }
        }

        reconf_model = {
            "Reconfiguration": {
                "AfterXConfigurations": {
                    "amount": 2,
                    "performAmount": 1,
                    "vp": "Model_0",
                    "description": {
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
                }
            }
        }

        reconf_predictor = {
            "Reconfiguration": {
                "AfterXConfigurations": {
                    "amount": 2,
                    "performAmount": 1,
                    "vp": "Predictor",
                    "description": {"WindowSize": 1,
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
                }
            }
        }

        one_min_stop = {"StopCondition": {
                "Instance": {
                    "TimeBasedSC": {
                        "Parameters": {
                            "MaxRunTime": 60,
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
                }
            }
        }

        # Only run using docker!!

        try:
            # Change optimizer, validator, surrogate, etc. during experiment - Passed
            self._base_experiment_description, self._base_search_space = \
                load_experiment_setup("./Resources/tests/test_cases_product_configurations/test_case_dynamic.json")
            experiment_description = self.base_experiment_description
            
            for reconf_skeleton in [reconf_optimizer, reconf_validator, reconf_surrogate, reconf_rep_manager]:
                experiment_description.update(deepcopy(reconf_skeleton))
                self.execute_experiment(experiment_description, number_of_repetitions=1)
            
            # Change sampling strategy, candidate selector and stop condition during the experiment for all test cases - Passed
            for reconf_skeleton in [reconf_sampling_and_candidate, reconf_stop_condition]:
                for exp_num in [1, 5]:
                    self._base_experiment_description, self._base_search_space = \
                        load_experiment_setup("./Resources/tests/test_cases_product_configurations/test_case_" + str(exp_num) + ".json")
                    experiment_description = self.base_experiment_description
                    experiment_description.update(deepcopy(reconf_skeleton))
                    self.execute_experiment(experiment_description, number_of_repetitions=1)
            
            # Turn of transfer learning, and predictor - Passed
            self._base_experiment_description, self._base_search_space = \
                load_experiment_setup("./Resources/tests/test_cases_product_configurations/test_case_0.json")
            experiment_description = self.base_experiment_description
            experiment_description.update(deepcopy(one_min_stop))
            
            for reconf_skeleton in [reconf_transfer_learning, reconf_predictor]:
                experiment_description.update(deepcopy(reconf_skeleton))
                self.execute_experiment(experiment_description, number_of_repetitions=1)
            
            # Change single optimizer
            self._base_experiment_description, self._base_search_space = \
                load_experiment_setup("./Resources/tests/test_cases_product_configurations/test_case_8.json")
            experiment_description = self.base_experiment_description
            experiment_description.update(deepcopy(reconf_single_optimizer))
            experiment_description.update(deepcopy(one_min_stop))
            self.execute_experiment(experiment_description, number_of_repetitions=1)
            
            # Change entire model and single surrogate - Passed
            self._base_experiment_description, self._base_search_space = \
                load_experiment_setup("./Resources/tests/test_cases_product_configurations/test_case_8.json")
            experiment_description = self.base_experiment_description
            experiment_description.update(deepcopy(one_min_stop))

            for reconf_skeleton in [reconf_model, reconf_single_surrogate]:
                experiment_description.update(deepcopy(reconf_skeleton))
                self.execute_experiment(experiment_description, number_of_repetitions=1)
        except KeyboardInterrupt:
            print("Stopped the benchmark!")

if __name__ == "__main__":
    runner = Runner()
    runner.clear_results()
    runner.run_benchmark()
    runner.show_results()