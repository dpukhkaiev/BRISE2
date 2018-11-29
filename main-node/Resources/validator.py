from jsonschema import validate
import json

# Calibrate directory //getcwd
from os import chdir
from os.path import abspath, join
from sys import path
path.append(join(abspath('.'), 'main-node'))
chdir(join(abspath('.'), 'main-node'))

from tools.file_system_io import load_json_file

def is_valid(file_path="resources/task.json"):
    """
    Validation function for json files.
    :file_path: string. The file for validation.
    :return: boolean. Is file valid
    """
    data = load_json_file(file_path)
    schema = load_json_file("resources/schema/task.schema.json") # validation schema

    return validate(data, schema) == None

if __name__ == "__main__":
   print("Valid:", is_valid())
