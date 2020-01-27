from selection.tests.test_selectors import TestSelector


def get_actual_result(selector_type: str): 
    # load EnergyExperiment and request more configurations, that there are in the search space, from selector (96 + 1 configurations)
    sobol_experiment_description_file = "./Resources/EnergyExperiment.json"
    used_selector, actual_result = TestSelector.get_actual_result(selector_type, sobol_experiment_description_file, number_of_configs=97, returned_points = []) 
    return used_selector, actual_result
