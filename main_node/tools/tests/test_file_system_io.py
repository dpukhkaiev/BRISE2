import pytest


class TestFileSystemIO:
    # this test set is aimed to cover the functionality of the 'file_system_io' tools

    def test_0_load_valid_json(self):
        # Test #0. Load content of a valid json file
        # Expected result: json file is loaded and can be treated as a python dictionary (get value from key)
        from tools.file_system_io import load_json_file
        input_file = "./Resources/SettingsBRISE.json"
        expected_result = "./Results/"
        actual_result = load_json_file(input_file)
        assert actual_result["General"]["results_storage"] == expected_result

    def test_1_load_invalid_json(self):
        # Test #1. Try to load content of non-json file
        # Expected result: an error is raised, that file can not be decoded
        import json

        from tools.file_system_io import load_json_file
        expected_result = "Expecting value"
        input_file = "./tools/file_system_io.py"
        with pytest.raises(json.JSONDecodeError) as excinfo:
            load_json_file(input_file)
        assert expected_result in str(excinfo.value)

    def test_2_load_non_existing_file(self):
        # Test #2. Try to load content of non-existing file
        # Expected result: an error is raised, that file doesn't exist
        from tools.file_system_io import load_json_file
        expected_result = "No such file or directory"
        input_file = "./Resources/no_such_file.json"
        with pytest.raises(IOError) as excinfo:
            load_json_file(input_file)
        assert expected_result in str(excinfo.value)

    def test_3_load_None_file(self):
        # Test #3. Try to load content if passed file parameter is None
        # Expected result: an error is raised
        from tools.file_system_io import load_json_file
        input_file = None
        expected_result = "expected str, bytes or os.PathLike object, not NoneType"
        with pytest.raises(TypeError) as excinfo:
            load_json_file(input_file)
        assert expected_result in str(excinfo.value)
