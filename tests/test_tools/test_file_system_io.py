from tools.file_system_io import load_json_file, create_folder_if_not_exists
import pytest



DATA_FOR_JSON_FILE = {
    "DomainDescription": {
        "HyperparameterNames": ["frequency", "threads"],
        "DataFile": "./Resources/GA/GAExperimentData.json"
    },
    "SelectionAlgorithm": {
        "SelectionType": "SobolSequence",
        "NumberOfInitialConfigurations": 10,
        "Step": 1
    },
    "TaskConfiguration": {
        "TaskName": "energy_consumption",
        "FileToRead": "Radix-500mio.csv",
        "ResultStructure": ["frequency", "threads", "energy"],
        "ResultDataTypes": ["float", "int", "float"],
        "Type": "student_deviation",
        "MaxTasksPerConfiguration": 4
    },
    "ModelCreation": {
        "SamplingSize": 64,
        "ModelTestSize": 0.9,
        "MinimumAccuracy": 0.85,
        "ModelType": "regression"
    }
}

def test_(tmpdir):
    with pytest.raises(IOError):
        load_json_file(path_to_file='GAExperimentDescription.json')

    file_path = tmpdir.join('GAExperimentDescription.json')
    file_path.write(DATA_FOR_JSON_FILE)

    # TODO - JSONDecodeError
    # assert load_json_file(path_to_file=file_path) == DATA_FOR_JSON_FILE


# TODO
# def test_create_folder_if_not_exists():

