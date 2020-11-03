import logging
import re
from os.path import abspath

from jsonschema import Draft4Validator, RefResolver
from jsonschema.exceptions import ValidationError
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

def get_duplicated_sc_names(validated_data: dict):
    """
    Validates if all Stop Condition names are unique.
    :validated_data: dict. Dictionary for validation.
    :return: list of duplicates.
    """
    sc_names = []
    for sc in validated_data["StopCondition"]:
        sc_names.append(sc["Name"])
    duplicates = []
    if len(sc_names) > len(set(sc_names)):
        duplicates = set([x for x in sc_names if sc_names.count(x) > 1])
    return duplicates

def get_missing_sc_entities(validated_data: dict):
    """
    Validates if all Stop Conditions defined in the Stop Condition Trigger Logic expression
    are present in the Experiment Description.
    :validated_data: dict. Dictionary for validation.
    :return: list of missing Stop Conditions.
    """
    sc_names = []
    for sc in validated_data["StopCondition"]:
        sc_names.append(sc["Name"])
    expression = validated_data["StopConditionTriggerLogic"]["Expression"]
    expression_components = re.sub(r"[^\w]", " ", expression).split()
    missing_components = []
    for component in expression_components:
        if component != "and" and component != "or" and component not in sc_names:
            missing_components.append(component)
    return missing_components


if __name__ == "__main__":
    # Basic unit test - load EnergyExperiment and check if it valid (should be valid).
    entity_description = load_json_file("Resources/EnergyExperiment.json")
    print("Valid:", is_json_file_valid(entity_description, './Resources/schema/experiment.schema.json'))
