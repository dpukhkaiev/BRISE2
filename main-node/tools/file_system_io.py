__doc__ = """
    Module to read data from files. Each function = 1 file type."""
import json
import logging
from os import path, makedirs


def load_json_file(path_to_file):
    """
    Method reads .json file
    :param path_to_file: sting path to file.
    :return: object that represent .json file
    """
    logger = logging.getLogger(__name__)
    try:
        with open(path_to_file, 'r') as File:
            jsonFile = json.loads(File.read())
            return jsonFile
    except IOError as error:
        logger.error("Error with reading %s file." % path_to_file, exc_info=True)
        raise error
    except json.JSONDecodeError as error:
        logger.error("Error with decoding json file: %s" % path_to_file, exc_info=True)
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
        logger.error("Unable to create folder: %s" % folderPath, exc_info=True)
        raise error
