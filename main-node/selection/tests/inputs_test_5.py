from selection.tests.test_selectors import TestSelector
from core_entities.configuration import Configuration


def get_actual_result(selector_type: str): 
    # load EnergyExperiment and request a single configuration from selector
    sobol_experiment_description_file = "./Resources/EnergyExperiment.json"
    disabled_configs = [Configuration([2200.0, 8], Configuration.Type.PREDICTED), Configuration([2200.0, 8], Configuration.Type.PREDICTED)]
    used_selector, actual_result = TestSelector.get_actual_result(selector_type, sobol_experiment_description_file, returned_points = [], disabled_configs = disabled_configs) 
    return used_selector, actual_result
