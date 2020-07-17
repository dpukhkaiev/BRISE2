from selection.tests.test_selectors import TestSelector


def get_actual_result(selector_type: str): 
    # load EnergyExperiment and request a single configuration from selector
    sobol_experiment_description_file = "./Resources/EnergyExperiment/EnergyExperiment.json"
    used_selector, actual_result = TestSelector.get_actual_result(selector_type, sobol_experiment_description_file, returned_points = []) 
    return used_selector, actual_result
