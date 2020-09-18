import pytest
from tools.initial_config import load_experiment_setup


@pytest.fixture(scope='function')
def get_sample():

    configurations_sample = [
        {'Params': {'experiment': 'energy', 'frequency': 2900.0, 'threads': 32}, 'Tasks': 10, 'Outliers': 1, 'Results': {'energy': 135.82333333333335}, 'STD': [1.5607289963347253]},
        {'Params': {'experiment': 'energy', 'frequency': 1300.0, 'threads': 25}, 'Tasks': 2, 'Outliers': 0, 'Results': {'energy': 173.135}, 'STD': [0.13435028842544242]},
        {'Params': {'experiment': 'energy', 'frequency': 2900.0, 'threads': 20}, 'Tasks': 4, 'Outliers': 0, 'Results': {'energy': 156.1475}, 'STD': [6.198598631948998]},
        {'Params': {'experiment': 'energy', 'frequency': 1900.0, 'threads': 20}, 'Tasks': 2, 'Outliers': 0, 'Results': {'energy': 151.53}, 'STD': [0.0]},
        {'Params': {'experiment': 'energy', 'frequency': 2800.0, 'threads': 4}, 'Tasks': 2, 'Outliers': 0, 'Results': {'energy': 358.61}, 'STD': [2.9981327522309678]},
        {'Params': {'experiment': 'energy', 'frequency': 1600.0, 'threads': 5}, 'Tasks': 2, 'Outliers': 0, 'Results': {'energy': 393.1}, 'STD': [4.73761543394986]},
        {'Params': {'experiment': 'energy', 'threads': 32, 'frequency': 2400.0}, 'Tasks': 2, 'Outliers': 0, 'Results': {'energy': 141.34}, 'STD': [0.7919595949289364]},
        {'Params': {'experiment': 'energy', 'threads': 2, 'frequency': 2400.0}, 'Tasks': 2, 'Outliers': 0, 'Results': {'energy': 672.7049999999999}, 'STD': [2.9344931419241562]},
        {'Params': {'experiment': 'energy', 'threads': 23, 'frequency': 1600.0}, 'Tasks': 2, 'Outliers': 0, 'Results': {'energy': 160.035}, 'STD': [0.8980256121069025]},
        {'Params': {'experiment': 'energy', 'threads': 18, 'frequency': 1900.0}, 'Tasks': 2, 'Outliers': 0, 'Results': {'energy': 160.14}, 'STD': [0.0]},
        {'Params': {'experiment': 'energy', 'threads': 13, 'frequency': 2700.0}, 'Tasks': 3, 'Outliers': 0, 'Results': {'energy': 174.64333333333332}, 'STD': [5.662590690958806]},
        {'Params': {'experiment': 'energy', 'threads': 8, 'frequency': 2400.0}, 'Tasks': 2, 'Outliers': 0, 'Results': {'energy': 233.565}, 'STD': [2.6940768363207477]},
        {'Params': {'experiment': 'energy', 'threads': 27, 'frequency': 2900.0}, 'Tasks': 10, 'Outliers': 0, 'Results': {'energy': 157.123}, 'STD': [23.189948037889184]},
        {'Params': {'experiment': 'energy', 'threads': 30, 'frequency': 2900.0}, 'Tasks': 2, 'Outliers': 0, 'Results': {'energy': 134.5}, 'STD': [1.0889444430272976]},
        {'Params': {'experiment': 'energy', 'threads': 29, 'frequency': 1900.0}, 'Tasks': 3, 'Outliers': 0, 'Results': {'energy': 138.92666666666665}, 'STD': [3.1326719160061014]},
        {'Params': {'experiment': 'energy', 'threads': 28, 'frequency': 2000.0}, 'Tasks': 2, 'Outliers': 0, 'Results': {'energy': 140.44}, 'STD': [0.7353910524340239]},
        {'Params': {'experiment': 'energy', 'threads': 27, 'frequency': 2700.0}, 'Tasks': 3, 'Outliers': 0, 'Results': {'energy': 141.92333333333335}, 'STD': [4.472385642286828]},
        {'Params': {'experiment': 'energy', 'threads': 9, 'frequency': 2200.0}, 'Tasks': 2, 'Outliers': 0, 'Results': {'energy': 217.36}, 'STD': [2.0364675298172736]},
        {'Params': {'experiment': 'energy', 'threads': 18, 'frequency': 1200.0}, 'Tasks': 2, 'Outliers': 0, 'Results': {'energy': 195.215}, 'STD': [1.138441917710351]},
        {'Params': {'experiment': 'energy', 'threads': 21, 'frequency': 2000.0}, 'Tasks': 2, 'Outliers': 0, 'Results': {'energy': 147.70999999999998}, 'STD': [0.9899494936611706]},
        {'Params': {'experiment': 'energy', 'threads': 2, 'frequency': 1700.0}, 'Tasks': 2, 'Outliers': 0, 'Results': {'energy': 848.19}, 'STD': [49.51161681868212]},
        {'Params': {'experiment': 'energy', 'threads': 10, 'frequency': 2901.0}, 'Tasks': 2, 'Outliers': 0, 'Results': {'energy': 245.12}, 'STD': [1.3859292911256387]},
        {'Params': {'experiment': 'energy', 'threads': 16, 'frequency': 2300.0}, 'Tasks': 2, 'Outliers': 0, 'Results': {'energy': 154.445}, 'STD': [1.788980156401966]},
        {'Params': {'experiment': 'energy', 'threads': 23, 'frequency': 2800.0}, 'Tasks': 3, 'Outliers': 1, 'Results': {'energy': 138.65}, 'STD': [0.04242640687119446]},
        {'Params': {'experiment': 'energy', 'threads': 17, 'frequency': 1900.0}, 'Tasks': 3, 'Outliers': 1, 'Results': {'energy': 158.66}, 'STD': [0.0]},
        {'Params': {'experiment': 'energy', 'threads': 16, 'frequency': 2700.0}, 'Tasks': 2, 'Outliers': 0, 'Results': {'energy': 161.14}, 'STD': [0.7778174593051983]},
        {'Params': {'experiment': 'energy', 'threads': 12, 'frequency': 2500.0}, 'Tasks': 5, 'Outliers': 1, 'Results': {'energy': 176.28250000000003}, 'STD': [4.601357589523625]},
        {'Params': {'experiment': 'energy', 'threads': 23, 'frequency': 2000.0}, 'Tasks': 3, 'Outliers': 0, 'Results': {'energy': 144.01}, 'STD': [3.396866202840496]},
        {'Params': {'experiment': 'energy', 'threads': 30, 'frequency': 2901.0}, 'Tasks': 4, 'Outliers': 0, 'Results': {'energy': 152.92000000000002}, 'STD': [6.79577810114486]},
        {'Params': {'experiment': 'energy', 'threads': 13, 'frequency': 2800.0}, 'Tasks': 2, 'Outliers': 0, 'Results': {'energy': 178.36}, 'STD': [0.7778174593051983]},
        {'Params': {'experiment': 'energy', 'threads': 1, 'frequency': 1300.0}, 'Tasks': 1, 'Outliers': 0, 'Results': {'energy': 1879.68}, 'STD': [float("nan")]}
    ]

    tasks_sample = [
        {'task id': '40838cb1-d580-4d36-90f3-862266f8eb18', 'worker': 'undefined', 'result': {'energy': 223.32, 'time': 0.52}, 'ResultValidityCheckMark': 'Outlier'},
        {'task id': '5f4f3b4a-3193-457b-aaed-4e595ed8d4d6', 'worker': 'undefined', 'result': {'energy': 226.29, 'time': 0.5}, 'ResultValidityCheckMark': 'OK'},
        {'task id': 'f9b94c98-413c-43a9-af89-8850caee1043', 'worker': 'undefined', 'result': {'energy': 392.65, 'time': 0.5}, 'ResultValidityCheckMark': 'OK'},
        {'task id': '001e5011-3a7a-452c-b51b-f7d2856652e4', 'worker': 'undefined', 'result': {'energy': 309.04, 'time': 0.51}, 'ResultValidityCheckMark': 'OK'},
        {'task id': 'e0a578b1-ddd4-4cdb-b77f-698f1a8eba77', 'worker': 'undefined', 'result': {'energy': 240.83, 'time': 0.51}, 'ResultValidityCheckMark': 'OK'},
        {'task id': '42e8e47f-f37f-4ca8-8c9e-e0518a894bb0', 'worker': 'undefined', 'result': {'energy': 426.29, 'time': 0.51}, 'ResultValidityCheckMark': 'OK'},
        {'task id': '2127f797-aada-4d2c-b769-e479e5d0fef6', 'worker': 'undefined', 'result': {'energy': 201.64, 'time': 0.52}, 'ResultValidityCheckMark': 'OK'},
        {'task id': '448472d0-4430-41ec-bb53-d04406c601f1', 'worker': 'undefined', 'result': {'energy': 392.65, 'time': 0.51}, 'ResultValidityCheckMark': 'OK'},
        {'task id': 'b1402cb2-cfd0-43ac-9659-5d4fb36cfdd4', 'worker': 'undefined', 'result': {'energy': 426.29, 'time': 0.52}, 'ResultValidityCheckMark': 'OK'},
        {'task id': 'd446a670-13c2-4a8e-a900-0e88fb7ea068', 'worker': 'undefined', 'result': {'energy': 201.64, 'time': 0.5}, 'ResultValidityCheckMark': 'OK'},
    ]

    experiment_description, search_space = load_experiment_setup("./Resources/EnergyExperiment/EnergyExperiment.json")
    yield configurations_sample, tasks_sample, experiment_description, search_space
