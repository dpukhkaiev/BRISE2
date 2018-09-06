from tools.file_system_io import load_json_file, create_folder_if_not_exists
import pytest


DATA_FOR_JSON_FILE = {
    "DomainDescription": {
        "FeatureNames": ["frequency", "threads"],
        "DataFile": "./Resources/taskData.json",
        "AllConfigurations": "# Will be loaded from DataFile and overwritten",
        "DefaultConfiguration": [2900.0, 32]

    },
    "SelectionAlgorithm": {
        "SelectionType": "SobolSequence",
        "NumberOfInitialExperiments": 10,
        "Step": 1
    },
    "ExperimentsConfiguration": {
        "TaskName": "energy_consumption",
        "FileToRead": "Radix-500mio.csv",
        "ResultStructure": ["frequency", "threads", "energy"],
        "ResultDataTypes": ["float", "int", "float"],
        "RepeaterDecisionFunction": "student_deviation",
        "MaxRepeatsOfExperiment": 4
    },
    "ModelCreation": {
        "ModelTestSize": 0.9,
        "MinimumAccuracy": 0.85,
        "ModelType": "regression",
        "FeaturesLabelsStructure": ["feature", "feature", "label"]
    }
}


def test_(tmpdir):
    with pytest.raises(IOError):
        load_json_file(path_to_file='task.json')

    file_path = tmpdir.join('task.json')
    file_path.write(DATA_FOR_JSON_FILE)

    # TODO - JSONDecodeError
    # assert load_json_file(path_to_file=file_path) == DATA_FOR_JSON_FILE


# TODO
# def test_create_folder_if_not_exists():

