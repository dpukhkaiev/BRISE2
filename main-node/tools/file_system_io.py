__doc__ = """
    Module to read data from files. Each function = 1 file type."""
import json
from os import path, makedirs


def load_json_file(path_to_file="./task.json"):
    """
    Method reads .json file
    :param path_to_file: sting path to file.
    :return: object that represent .json file
    """
    try:
        with open(path_to_file, 'r') as File:
            jsonFile = json.loads(File.read())
            return jsonFile
    except IOError as e:
        raise e


def create_folder_if_not_exists(folderPath):
    """
    Method create folder if it don't exist.
    :param path: sting path to folder.
    :return: true if create folder or it exist
    """
    try:
        if not path.exists(path.dirname(folderPath)):
            makedirs(path.dirname(folderPath))
        return True
    except IOError as e:
        raise e
    except json.JSONDecodeError as e:
        raise e

