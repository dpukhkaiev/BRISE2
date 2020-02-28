__doc__ = """
    Module to read data from files. Each function = 1 file type."""
import json
import logging
from tools.front_API import API


def load_json_file(path_to_file):
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

