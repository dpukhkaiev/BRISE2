import pytest
import timeit
import os

from reconfiguration.reconfiguration_module import ReconfigurationModule
from reconfiguration.effector import Effector
from core_entities.experiment import Experiment
from configuration_selection.configuration_selection import ConfigurationSelection

ITERATIONS = 100

class TestApproachPerformance:

    @pytest.fixture(scope='function')
    def reconf_module(self, get_experiment):
        return self._get_reconf_module(get_experiment)
    
    @pytest.fixture(scope='function')
    def reconf_module_multi_models(self, get_experiment):
        return self._get_reconf_module(get_experiment, experiment_num=8)
    
    @pytest.fixture(scope='function')
    def reconf_module_multi_features_single_model(self, get_experiment):
        return self._get_reconf_module(get_experiment, experiment_num=3)

    def _get_reconf_module(self, get_experiment, experiment_num:int = 0):
        """Make a separate function out of it to reuse it for diffrent experiment numbers"""
        Effector.clear_all()

        experiment_description, search_space = get_experiment(experiment_num)
        experiment = Experiment(experiment_description, search_space)
        cs = ConfigurationSelection(experiment)
        return ReconfigurationModule(experiment, cs)
    
    @pytest.mark.skip(reason="Just for measuring")
    def test_change_surrogate(self, reconf_module:ReconfigurationModule):
        start = timeit.default_timer()

        # Change
        iterations = 100
        for i in range(iterations):
            desc = {"Instance": {
                            "LinearRegression": {
                                "MultiObjective": False,
                                "Type": "sklearn_model_wrapper",
                                "Class": "sklearn.linear_model.LinearRegression"
                            }
                        }}
            reconf_module.change_variant("Surrogate", desc)
            reconf_module.done().reconfigure()

        end = timeit.default_timer()
        duration = end - start

        self.save_result("surrogate", iterations, duration)

    @pytest.mark.skip(reason="Just for measuring")
    def test_change_single_surrogate(self, reconf_module_multi_features_single_model:ReconfigurationModule):
        reconf_module = reconf_module_multi_features_single_model

        # Change
        start = timeit.default_timer()
        iterations = ITERATIONS
        for i in range(iterations):
            surrogate_desc = {"Instance": {"ModelMock": {
                                "MultiObjective": True,
                                "Type": "model_mock"
                            }
                        }}
            reconf_module.change_variant("Surrogate_0", surrogate_desc)
            reconf_module.done().reconfigure()

            surrogate_desc = {"Instance": {
                        "LinearRegression": {
                            "MultiObjective": False,
                            "Type": "sklearn_model_wrapper",
                            "Class": "sklearn.linear_model.LinearRegression"
                        }
                    }}
            reconf_module.change_variant("Surrogate_0", surrogate_desc)
            reconf_module.done().reconfigure()
        end = timeit.default_timer()
        duration = end - start

        print("Time for", iterations * 2, "changes took", duration, "seconds")
        self.save_result("single_surrogate", iterations * 2, duration)
        #assert False

    @pytest.mark.skip(reason="Just for measuring")
    def test_change_single_optimizer(self, reconf_module_multi_features_single_model:ReconfigurationModule):
        """Test to change a single optimizer"""
        reconf_module = reconf_module_multi_features_single_model
        
        # Change
        start = timeit.default_timer()
        iterations = ITERATIONS
        for i in range(iterations):
            optimizer_desc = {"Instance": {
                            "RandomSearch": {
                                "SamplingSize": 500,
                                "MultiObjective": True,
                                "Type": "random_search"
                            }
                        }}
            reconf_module.change_variant("Optimizer_0", optimizer_desc)
            reconf_module.done().reconfigure()

            optimizer_desc = {"Instance": {
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
                        }}
            reconf_module.change_variant("Optimizer_0", optimizer_desc)
            reconf_module.done().reconfigure()

        end = timeit.default_timer()
        duration = end - start

        print("Time for", iterations * 2, "changes took", duration, "seconds")
        self.save_result("single_optimizer", iterations * 2, duration)
        #assert False

    @pytest.mark.skip(reason="Just for measuring")
    def test_change_single_surrogate_on_multiple_models(self, reconf_module_multi_models:ReconfigurationModule):
        """Test to change a single surrogate on a experiment with multiple models"""
        reconf_module = reconf_module_multi_models

        # Change
        start = timeit.default_timer()
        iterations = ITERATIONS
        for i in range(iterations):
            surrogate_desc = {"Instance": {"ModelMock": {
                                "MultiObjective": True,
                                "Type": "model_mock"
                            }
                        }}
            reconf_module.change_variant("Surrogate_0", surrogate_desc, ["Model_1"])
            reconf_module.done().reconfigure()
            
            surrogate_desc = {"Instance": {
                            "LinearRegression": {
                                "MultiObjective": False,
                                "Type": "sklearn_model_wrapper",
                                "Class": "sklearn.linear_model.LinearRegression"
                            }
                        }}
            reconf_module.change_variant("Surrogate_0", surrogate_desc, ["Model_1"])
            reconf_module.done().reconfigure()
        
        end = timeit.default_timer()
        duration = end - start

        print("Time for", iterations * 2, "changes took", duration, "seconds")
        self.save_result("single_optimizer_multi_model", iterations * 2, duration)
        #assert False

    def save_result(self, test_name, total_changes, time):
        path = os.path.dirname(os.path.abspath(__file__))
        with open(path + "/performance_results.txt", "a", encoding="utf-8") as file:
            file.write(f"--- {test_name} ---\n"+
                       f"Changes: {total_changes}\n"+
                       f"Time: {time} seconds\n")
            file.close()

        # Write CSV
        with open(path + "/performance_results.csv", "a", encoding="utf-8") as file:
            file.write(f"{test_name}, {total_changes}, {time}\n")
            file.close()