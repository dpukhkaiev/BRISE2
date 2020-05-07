import pytest
import os

from selection.selection_algorithms import get_selector
from core_entities.experiment import Experiment
from core_entities.configuration import Configuration
from tools.initial_config import load_experiment_setup

os.environ["TEST_MODE"] = 'UNIT_TEST'

class TestSelector:
    # This test set is aimed to cover the logic of new configurations selection from the search space.
    # Common workflow for all selector tests:
    # 1. Load ExperimentSetup and ExperimentDescription
    # 2. Modify ExperimentSetup to use proper selector
    # 3. Create an instance of Experiment and Selector
    # 4. Get a number of configurations, that was requested
    # 5. Return gotten configurations and class name of used selector

    ########################
    # Sobol selector tests #
    ########################

    def test_0_get_new_point(self):
        # Test #0. Get point without Nones from Sobol selector if no points were gotten yet        
        # 'inputs_test_0.py' is used, that loads EnergyExperiment and requests a single configuration from selector
        # As SobolSequence is determinated selector, we expect to get a specific configuration [2200.0, 8] as a first one for EnergyExperiment
        from selection.tests.inputs_test_0 import get_actual_result
        expected_result = Configuration([2200.0, 8], Configuration.Type.FROM_SELECTOR)
        used_selector, actual_result = get_actual_result("SobolSequence")
        assert actual_result == expected_result
        assert used_selector == "SobolSequence"

    #####################
    # CS selector tests #
    #####################

    def test_2_get_new_point(self):
        # Test #2. Get point without Nones from ConfigSpace selector if no points were gotten yet
        # 'inputs_test_0.py' is used, that loads EnergyExperiment and requests a single configuration from selector
        # ConfigSpace selector is non-determinated one, thus it is expected to get some valid configuration without None values of the type 'FROM_SELECTOR'
        from selection.tests.inputs_test_0 import get_actual_result
        used_selector, actual_result = get_actual_result("ConfigSpaceSelector")
        assert isinstance(actual_result, Configuration)
        for param in actual_result.parameters:
            assert param is not None
        assert actual_result.type == Configuration.Type.FROM_SELECTOR
        assert used_selector == "ConfigSpaceSelector"

    #####################
    # invalid selector  #
    #####################

    def test_6_invalid_selector_name(self):
        # Test #6. Check, how invalid selector name specified in ExperimentSetup is handled
        # The aim of this test is to check the logic of choosing selector class
        # If invalid selector name is specified, an Exception is expected
        # please note, that invalid selector names are basically handled preliminary by 'sel_algorithm.schema.json'
        from selection.tests.inputs_test_0 import get_actual_result
        expected_result = "does not contain any classes!"
        with pytest.raises(NameError) as excinfo:
            get_actual_result("Invalid")
        assert expected_result in str(excinfo.value)

    def test_7_semi_valid_selector_name(self):
        # Test #7. Find selector with partially correct name
        # This test is aimed to check the logic of choosing selector class, if its name is only partially correct
        # According to the logic of 'reflective_class_import' used, if name is partially correct, valid class load is expected
        # In this test Sobol selector should be chosen from its partial name
        from selection.tests.inputs_test_0 import get_actual_result
        expected_result = Configuration([2200.0, 8], Configuration.Type.FROM_SELECTOR)
        used_selector, actual_result = get_actual_result("Sobol")
        assert actual_result == expected_result
        assert used_selector == "SobolSequence"

    @staticmethod
    def get_actual_result(selector_type: str, experiment_description_file: str, number_of_configs: int = 1,
                          returned_points: list = []):
        '''
        This method incapsulates common functionality for all tests: Experiment and Selector instantiation and initialization,
        requesting Configuration(s) from Selector and adding them to the Experiment

        :param selector_type: str. Type of Selector to be instantiated
        :param experiment_description_file: str. Experiment description to initialize Experiment
        :param number_of_configs: int. Quantity of Configurations, that are requested from Selector
        :param returned_points: list of Configurations. Those Configurations, that were already returned by Selector (according to some tests' intention)
        :param disabled_configs: list of Configurations. Those Configurations, that were already returned by other instances, e.g. model (according to some tests' intention)
        :returns: used_selector, actual_result. The type of Selector, that was instantiated and Configuration(s) that were returned by Selector
        '''
        experiment_description, search_space = load_experiment_setup(experiment_description_file)
        experiment_description["SelectionAlgorithm"]["SelectionType"] = selector_type
        experiment = Experiment(experiment_description, search_space)
        # add configs already returned by selector to the experiment
        for returned_point in returned_points:
            experiment.evaluated_configurations.append(returned_point)
        # add configs predicted by model to the experiment
        selector = get_selector(experiment=experiment)
        for _ in range(0, number_of_configs):
            actual_result = selector.get_next_configuration()
            experiment.evaluated_configurations.append(actual_result)
        used_selector = selector.__class__.__name__
        return used_selector, actual_result
