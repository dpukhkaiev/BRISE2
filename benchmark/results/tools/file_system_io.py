__doc__ = """
    Module to read data from files. Each function = 1 file type."""
import json
import logging
from os import path, makedirs
from tools.front_API import API


def load_json_file(path_to_file) -> dict:
    """
    Method reads .json file
    :param path_to_file: sting path to file.
    :return: object that represent .json file
    """
    logger = logging.getLogger(__name__)
    front_api = API()
    try:
        with open(path_to_file, 'r') as File:
            jsonFile = json.loads(File.read())
            return jsonFile
    except IOError as error:
        msg = "Unable to read a json file '%s'. Error information: %s" % (path_to_file, error)
        logger.error(msg, exc_info=True)
        front_api.send('log', 'error', message=msg)
        raise error
    except json.JSONDecodeError as error:
        msg = "Unable to decode a json file '%s'. Error information: %s" % (path_to_file, error)
        logger.error(msg, exc_info=True)
        front_api.send('log', 'error', message=msg)
        raise error


def create_folder_if_not_exists(folderPath):
    """
    Method create folder if it don't exist.
    :param folderPath: sting path to folder, could include filename.
    :return: true if create folder or it exist
    """
    logger = logging.getLogger(__name__)
    try:
        dir_path = path.dirname(folderPath)
        if dir_path:
            if not path.exists(path.dirname(folderPath)):
                makedirs(path.dirname(folderPath))
        return True
    except IOError as error:
        msg = "Unable to create folder %s. Error information: %s" % (folderPath, error)
        logger.error(msg, exc_info=True)
        API().send("log", "error", message=msg)
        raise error
