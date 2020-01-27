from selection.tests.test_selectors import TestSelector
from core_entities.configuration import Configuration


def get_actual_result(selector_type: str): 
    # load EnergyExperiment, add one configuration to experiment manually and request next configuration from selector
    sobol_experiment_description_file = "./Resources/EnergyExperiment.json"
    already_added_config = Configuration([2200.0, 8], Configuration.Type.FROM_SELECTOR)
    used_selector, actual_result = TestSelector.get_actual_result(selector_type, sobol_experiment_description_file, returned_points=[already_added_config]) 
    return used_selector, actual_result
