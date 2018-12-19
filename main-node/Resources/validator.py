from jsonschema import validate, RefResolver, Draft4Validator
import json


# from os import chdir
from os.path import abspath
# from sys import path
# path.append(join(abspath('.'), 'main-node'))
# chdir(join(abspath('.'), 'main-node'))

from tools.file_system_io import load_json_file


def is_experiment_description_valid(schema_path="resources/schema/task.schema.json", 
                                    file_path="resources/task.json"):
    """
    Validation function for json files.
    :schema_path: string. The template schema for validation.
    :file_path: string. The file for validation.
    :return: boolean. Is file valid
    """
    entity_description = load_json_file(file_path)
    schema = load_json_file(schema_path)
    
    resolver = RefResolver('file:///' + abspath('.').replace("\\", "/") + '/', schema)

    return Draft4Validator(schema, resolver=resolver).validate(entity_description) == None


if __name__ == "__main__":
    print("Valid:", is_experiment_description_valid())
