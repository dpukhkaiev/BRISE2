import pytest

from tools.initial_config import load_experiment_setup, validate_experiment_description, validate_experiment_data
from tools.file_system_io import load_json_file


class TestInitialConfig:
    # this test set is aimed to cover the functionality of the 'initial_config' tools

    def test_0_load_valid_experiment_setup(self):
        # Test #0. Load an Experiment setup from the valid Experiment description file
        # Expected result: both experiment description and search space are loaded. Experiment description can be used as a dictionary
        from core_entities.search_space import SearchSpace
        input_file = "./Resources/EnergyExperiment.json"
        expected_experiment = "energy_consumption"
        actual_experiment_description, actual_search_space = load_experiment_setup(input_file)
        assert actual_experiment_description["TaskConfiguration"]["TaskName"] == expected_experiment
        assert isinstance(actual_search_space, SearchSpace)

    def test_1_load_invalid_experiment_setup(self):
        # Test #1. Try to load an Experiment setup from the invalid Experiment description file
        # Expected result: error raised
        input_file = "./Resources/SettingsBRISE.json"
        with pytest.raises(KeyError):
            load_experiment_setup(input_file)
        
    def test_2_load_non_existing_experiment_setup(self):\
        # Test #2. Try to load an Experiment setup from the non existing file
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

    def test_4_validate_valid_experiment_description(self, caplog):
        # Test #4. Validate an experiment description, loaded from the valid Experiment description file
        # Expected result: experiment description is valid (logged statement)
        import logging
        caplog.set_level(logging.INFO)
        task_description = load_json_file("./Resources/EnergyExperiment.json")
        framework_settings = load_json_file('./Resources/SettingsBRISE.json')
        input_description = {**task_description, **framework_settings}
        expected_result = "Provided Experiment Description is valid."
        validate_experiment_description(input_description)
        for record in caplog.records:
            assert record.levelname == "INFO"
            assert expected_result in str(record)

    def test_5_validate_invalid_experiment_description(self):
        # Test #5. Validate an experiment description, loaded from the invalid Experiment description file
        # Note: SettingsBRISE.json is not enough to pass the scheme. File is treated as invalid. Both (settings and ED) must be provided
        # Expected result: experiment description is invalid, error is raised
        input_description = load_json_file("./Resources/SettingsBRISE.json")
        expected_result = "Some errors caused during validation. Please, check the Experiment Description."
        with pytest.raises(ValueError) as excinfo:
            validate_experiment_description(input_description)
        assert expected_result in str(excinfo.value)

    def test_6_validate_valid_experiment_data(self, caplog):
        # Test #6. Validate an experiment data, loaded from the valid Experiment data file
        # Expected result: experiment data is valid (logged statement)
        import logging
        caplog.set_level(logging.INFO)
        input_data = load_json_file("./Resources/EnergyExperimentData.json")
        expected_result = "Provided Experiment Data is valid."
        validate_experiment_data(input_data)
        for record in caplog.records:
            assert record.levelname == "INFO"
            assert expected_result in str(record)
    
    def test_7_validate_invalid_experiment_data(self):
        # Test #7. Validate an experiment data, loaded from the invalid Experiment data file
        # Expected result: experiment data is invalid, error is raised
        input_data = load_json_file("./Resources/EnergyExperiment.json")
        expected_result = "Provided Experiment Data has not passed the validation using schema in file"
        with pytest.raises(ValueError) as excinfo:
            validate_experiment_data(input_data)
        assert expected_result in str(excinfo.value)
