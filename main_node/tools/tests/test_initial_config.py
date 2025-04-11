import pytest

from tools.initial_config import load_experiment_setup


class TestInitialConfig:
    # this test set is aimed to cover the functionality of the 'initial_config' tools

    def test_0_load_valid_experiment_setup(self):
        # Test #0. Load an Experiment setup from the valid Experiment description file
        # Expected result: both experiment description and search space are loaded.
        # Experiment description can be used as a dictionary
        from core_entities.search_space import SearchSpace
        input_file = "./Resources/tests/test_cases_product_configurations/test_case_0.json"
        expected_experiment = "test"
        actual_experiment_description, actual_search_space = load_experiment_setup(input_file)
        assert actual_experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        assert isinstance(actual_search_space, SearchSpace)

    def test_1_load_invalid_experiment_setup(self):
        # Test #1. Try to load an Experiment setup from the invalid Experiment description file
        # Expected result: error raised
        input_file = "./Resources/SettingsBRISE.json"
        with pytest.raises(KeyError):
            load_experiment_setup(input_file)

    def test_2_load_non_existing_experiment_setup(self):
        # Test #2. Try to load an Experiment setup from the non-existing file
        # Expected result: FileNotFoundError error raised
        input_file = "./Resources/non_existing_path"
        expected_result = "No such file or directory"
        with pytest.raises(FileNotFoundError) as excinfo:
            load_experiment_setup(input_file)
        assert expected_result in str(excinfo.value)

    def test_3_load_None_experiment_setup(self):
        # Test #3. Try to load an Experiment setup if file parameter is empty
        # Expected result: TypeError error raised
        input_file = None
        expected_result = "expected str, bytes or os.PathLike object, not NoneType"
        with pytest.raises(TypeError) as excinfo:
            load_experiment_setup(input_file)
        assert expected_result in str(excinfo.value)