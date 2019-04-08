from os.path import abspath
import logging
import json

from jsonschema import validate, RefResolver, Draft4Validator

from jsonschema.exceptions import ValidationError

# # [ Uncomment in emergency case ]
# # ImportError: No module named tools.file_system_io
# from os import chdir, getcwd
# from sys import path
# chdir('..')
# path.append(abspath('.'))
# print(getcwd())
# print("----------------")
from tools.file_system_io import load_json_file

def is_experiment_description_valid(schema_path="Resources/schema/task.schema.json", 
                                    file_path="Resources/task.json"):
    """
    Validation function for json files.
    :schema_path: string. The template schema for validation.
    :file_path: string. The file for validation.
    :return: boolean. Is file valid
    """
    entity_description = load_json_file(file_path)
    schema = load_json_file(schema_path)
    
    resolver = RefResolver('file:///' + abspath('.').replace("\\", "/") + '/', schema)

    try:
        return Draft4Validator(schema, resolver=resolver).validate(entity_description) == None
    except ValidationError as e:
        logging.getLogger(__name__).error(e)
        return False


if __name__ == "__main__":
    print("Valid:", is_experiment_description_valid())
