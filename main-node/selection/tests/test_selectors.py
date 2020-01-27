import pytest

from selection.selection_algorithms import get_selector
from core_entities.experiment import Experiment
from core_entities.configuration import Configuration
from tools.initial_config import load_experiment_setup


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

    def test_1_get_point_Nones(self):
        # Test #1. Get point containing inactive dependent parameters (None values) from Sobol selector
        # The aim of this test is to check, how selector deals with dependent parameters (it shouldn't miss any condition and produce None values properly)
        # 'inputs_test_1.py' is used, that loads NBExperiment and requests a single configuration from selector
        # As SobolSequence is determinated selector, we expect to get a specific configuration containing None values as a first one for NBExperiment
        from selection.tests.inputs_test_1 import get_actual_result
        expected_result = Configuration(['false', 'greedy', None, 500.0005, 500.0005, 500, 'false', None], Configuration.Type.FROM_SELECTOR)
        used_selector, actual_result = get_actual_result("SobolSequence")
        assert actual_result == expected_result
        assert used_selector == "SobolSequence"
    
    def test_2_get_next_point(self):
        # Test #2. Get point from Sobol selector if some points are already gotten (check duplicates)
        # 'inputs_test_2.py' is used, that loads EnergyExperiment, adds manually some configs to the experiment and requests a configuration from selector
        # As SobolSequence is determinated selector, we expect to get next configuration without duplicating those already added to the experiment
        from selection.tests.inputs_test_2 import get_actual_result
        expected_result = Configuration([2700.0, 2], Configuration.Type.FROM_SELECTOR)
        used_selector, actual_result = get_actual_result("SobolSequence")
        assert actual_result == expected_result
        assert used_selector == "SobolSequence"

    def test_3_get_point_full_search_space(self):
        # Test #3. Get config from Sobol selector if all configs from Search space were already gotten
        # 'inputs_test_3.py' is used, that loads EnergyExperiment (which has finite search space, containing 96 configs) and request 97 configs from selector
        # Expected behavior of the selector - raise an Exception, signalizing that the whole search space was already explored
        from selection.tests.inputs_test_3 import get_actual_result
        expected_result = "The whole search space was already explored. Selector can not find new points"
        with pytest.raises(ValueError) as excinfo:
            get_actual_result("SobolSequence")
        assert expected_result in str(excinfo.value)

    #####################
    # CS selector tests #
    #####################

    def test_4_get_new_point(self):
        # Test #4. Get point without Nones from ConfigSpace selector if no points were gotten yet
        # 'inputs_test_0.py' is used, that loads EnergyExperiment and requests a single configuration from selector
        # ConfigSpace selector is non-determinated one, thus it is expected to get some valid configuration without None values of the type 'FROM_SELECTOR'
        from selection.tests.inputs_test_0 import get_actual_result
        used_selector, actual_result = get_actual_result("ConfigSpaceSelector")
        assert isinstance(actual_result, Configuration)
        for param in actual_result.parameters:
            assert param is not None
        assert actual_result.type == Configuration.Type.FROM_SELECTOR
        assert used_selector == "ConfigSpaceSelector"

    def test_5_get_point_Nones(self):
        # Test #5. Get point containing inactive dependent parameters (None values) from ConfigSpace selector
        # 'inputs_test_1.py' is used, that loads NBExperiment and requests a single configuration from selector
        # ConfigSpace selector is non-determinated one, so it is expected to get some valid configuration of type 'FROM_SELECTOR'
        from selection.tests.inputs_test_1 import get_actual_result
        used_selector, actual_result = get_actual_result("ConfigSpaceSelector")
        assert isinstance(actual_result, Configuration)
        assert actual_result.type == Configuration.Type.FROM_SELECTOR
        assert used_selector == "ConfigSpaceSelector"
    
    def test_6_get_next_point(self):
        # Test #6. Get point from ConfigSpace selector if this point is already gotten (check duplicates)
        # 'inputs_test_2.py' is used, that loads EnergyExperiment, adds manually some configs to the experiment and requests a configuration from selector
        # It is expected to get new configuration that was not added to the experiment yet
        from selection.tests.inputs_test_2 import get_actual_result
        already_added_config = Configuration([2200.0, 8], Configuration.Type.FROM_SELECTOR)
        used_selector, actual_result = get_actual_result("ConfigSpaceSelector")
        assert actual_result != already_added_config
        assert used_selector == "ConfigSpaceSelector"

    def test_7_get_point_full_search_space(self):
        # Test #7. Get config from ConfigSpace selector if all configs from Search space were already gotten
        # 'inputs_test_3.py' is used, that loads EnergyExperiment (which has finite search space, containing 96 configs) and request 97 configs from selector
        # Expected behavior of the selector - raise an Exception, signalizing that the whole search space was already explored
        from selection.tests.inputs_test_3 import get_actual_result
        expected_result = "The whole search space was already explored. Selector can not find new points"
        with pytest.raises(ValueError) as excinfo:
            get_actual_result("ConfigSpaceSelector")
        assert expected_result in str(excinfo.value)

    #####################
    # invalid selector  #
    #####################

    def test_8_invalid_selector_name(self):
        # Test #8. Check, how invalid selector name specified in ExperimentSetup is handled
        # The aim of this test is to check the logic of choosing selector class
        # If invalid selector name is specified, an Exception is expected
        # please note, that invalid selector names are basically handled preliminary by 'sel_algorithm.schema.json'
        from selection.tests.inputs_test_0 import get_actual_result
        expected_result = "does not contain any classes!"
        with pytest.raises(NameError) as excinfo:
            get_actual_result("Invalid")
        assert expected_result in str(excinfo.value)

    def test_9_semi_valid_selector_name(self):
        # Test #9. Find selector with partially correct name
        # This test is aimed to check the logic of choosing selector class, if its name is only partially correct
        # According to the logic of 'reflective_class_import' used, if name is partially correct, valid class load is expected
        # In this test Sobol selector should be chosen from its partial name
        from selection.tests.inputs_test_0 import get_actual_result
        expected_result = Configuration([2200.0, 8], Configuration.Type.FROM_SELECTOR)
        used_selector, actual_result = get_actual_result("Sobol")
        assert actual_result == expected_result
        assert used_selector == "SobolSequence"

    ########################################
    # configs from other sources disabling #
    ########################################

    def test_10_disable_configuration_predicted_by_model(self):
        # Test #10. Some configurations may be retrieved from other sources (e.g. predicted by model). Such configurations should be disabled, 
        # that prevents selector from picking them again. This test checks selector's behavior in case of external config being disabled
        # (selector type is not important here, as disabling functionality is common for both)
        # 'inputs_test_4.py' is used, that loads EnergyExperiment and imitates point to be predicted by the model
        # Expected behavior of the selector - disable this point and select the next one, which was not retrieved before
        from selection.tests.inputs_test_4 import get_actual_result
        expected_result = Configuration([2700.0, 2], Configuration.Type.FROM_SELECTOR)
        used_selector, actual_result = get_actual_result("SobolSequence")
        assert actual_result == expected_result
        assert used_selector == "SobolSequence"

    def test_11_disable_same_configuration_predicted_by_model_again(self, caplog):
        # Test #11. For some reason configuration from other sources can repeat. They should be disabled only once
        # 'inputs_test_5.py' is used, that loads EnergyExperiment and imitates 2 points to be predicted by the model
        # Expected behavior of the selector - disable point once and emit warning on repeated disabling. Select new point
        from selection.tests.inputs_test_5 import get_actual_result
        expected_result = Configuration([2700.0, 2], Configuration.Type.FROM_SELECTOR)
        used_selector, actual_result = get_actual_result("SobolSequence")
        assert actual_result == expected_result
        assert used_selector == "SobolSequence"
        for record in caplog.records:
            assert record.levelname == "WARNING"
        assert "Trying to disable configuration that have been already retrieved (or disabled)." in caplog.text
        
    @staticmethod
    def get_actual_result(selector_type: str, experiment_description_file: str, number_of_configs: int = 1, returned_points: list = [], disabled_configs: list = []):
        experiment_description, search_space = load_experiment_setup(experiment_description_file)
        experiment_description["SelectionAlgorithm"]["SelectionType"] = selector_type
        experiment = Experiment(experiment_description, search_space)
        selector = get_selector(experiment=experiment)
        selector.returned_points = returned_points
        for configuration in disabled_configs:
            selector.disable_configuration(configuration)
        for _ in range(0, number_of_configs):
            actual_result = selector.get_next_configuration()
        used_selector = selector.__class__.__name__
        return used_selector, actual_result
