from typing import Dict, Tuple

from configuration_selection.model.validator.validator_abs import Validator
from tools.reflective_class_import import reflective_class_import


class ValidatorOrchestrator:

    def get_validator(self, validator_description: Dict, region: Tuple, objectives: Dict) -> Validator:
        keys = list(validator_description.keys())
        assert len(keys) == 1
        feature_name = keys[0]

        validator_class = reflective_class_import(validator_description[feature_name]["Type"], "configuration_selection/model/validator")
        return validator_class(validator_description[feature_name], region, objectives)
