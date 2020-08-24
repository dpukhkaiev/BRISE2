from os.path import abspath
import logging

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


def is_json_file_valid(validated_data: dict, schema_path):
    """
    Validates if dictionary suites provided schema.
    :validated_data: dict. Dictionary for validation.
    :schema_path: string. The template schema for validation.
    :return: boolean. Is dictionary is valid under provided schema.
    """
    schema = load_json_file(schema_path)
    
    resolver = RefResolver('file:///' + abspath('.').replace("\\", "/") + '/', schema)

    try:
        return Draft4Validator(schema, resolver=resolver).validate(validated_data) is None
    except ValidationError as error:
        logging.getLogger(__name__).error(error)
        return False


if __name__ == "__main__":
    # Basic unit test - load EnergyExperiment and check if it valid (should be valid).
    entity_description = load_json_file("Resources/EnergyExperiment.json")
    print("Valid:", is_json_file_valid(entity_description, './Resources/schema/experiment.schema.json'))
