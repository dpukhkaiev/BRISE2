__doc__ = """
Main module for running benchmark 

Requirements: 
    -   sklearn(with all deps like numpy, scipy : 0.19.1   
    -   sobol_seq
    -   
"""


from WSClient import WSClient
from regression import Regression
from repeater.repeater_selection import get_repeater
from tools.initial_config import initialize_config
from tools.features_tools import split_features_and_labels
from selection.selection_algorithms import get_selector

import urllib.parse
import json
import numpy
import itertools

# disable warnings for demonstration.
from warnings import filterwarnings
filterwarnings("ignore")

def run():
    globalConfig, task = initialize_config()
    # Creating instance of selector based on selection type and task data for further uniformly distributed data points generation.
    selector = get_selector(selector_type=task["params"]["SelectionType"], dimensionality=len(task["TaskDataPoints"]), data=task["TaskDataPoints"])
    #   Connect to the Worker Service and send task.
    WS = WSClient(task_name=task["task_name"],
                  task_params=task["params"],
                  ws_addr=globalConfig["WorkerService"]["Address"],
                  logfile='%s%s_WSClient.csv' % (globalConfig['results_storage'], task['params']["FileToRead"]))

    #begin repiter module
    # Creating runner for experiments that will repeat task running for avoiding fluctuations.
    repeater = get_repeater("default", WS)

    # Need to find default value that we will used in regression to evaluate solution
    print("Getting default value..")
    
    default_result = repeater.measure_task([task["default_point"]]) #change it to switch inside and devide to
    default_features, default_value = split_features_and_labels(default_result, task["params"]["ResultFeatLabels"])
    print(default_value)

    # Creating initial set of points for testing and first attempt to create regression model.
    initial_task = selector.merge_data_with_selection_algorithm(numOfPoints=task["params"]["NumberOfInitialExperiments"])

    # Results will be in a list of points, each point is also a list of values:
    # [[val1, val2,... valN], [val1, val2,... valN]...]
    print("Sending initial task..")
    repeater = get_repeater(task["params"]["DecisionFunction"], WS)
    results = repeater.measure_task(initial_task, default_point=default_result[0])
    print("Results got, splitting to features and labels..")
    features, labels = split_features_and_labels(results, task["params"]["ResultFeatLabels"])

    # Generate whole search space for regression.
    search_space = list(itertools.product(*task["TaskDataPoints"]))




    #todo begin Stop conditions
    reg_success = False
    while not reg_success:
        # print(features)
        # print(labels)
        reg = Regression(output_filename = "%s%s_regression.txt" % (globalConfig['results_storage'], task['params']["FileToRead"]),
                         test_size = task["params"]["ModelTestSize"],
                         features = features,
                         targets = labels)

        reg_success = reg.regression(param=task["params"],
                                     score_min=0.85,
                                     searchspace=search_space)
        #new file
        if reg_success:
            print("Model build with accuracy: %s" % reg.accuracy)
            print("Verifying solution that model gave..")
            measured_energy = split_features_and_labels(repeater.measure_task([reg.solution_features]), task["params"]["ResultFeatLabels"])[1][0]

            # If our measured energy higher than default best value - add this point to data set and rebuild model.
            if measured_energy > default_value[0]:
                features += [reg.solution_features]
                labels += [measured_energy]
                print("Predicted energy larger than default.")
                print("Predicted energy: %s. Measured: %s. Best default: %s" %(reg.solution_labels[0], measured_energy[0], default_value[0][0]))
                reg_success = False
                continue

        if not reg_success:
            print("New data point needed to continue building regression. Current number of data points: %s" % str(selector.numOfGeneratedPoints))
            print('='*100)
            # cur_task = [sobol.getNextPoint()]
            cur_task = [selector.get_next_point() for x in range(task['params']['step'])]
            if reg.feature_result:
                cur_task.append(reg.feature_result)
            results = repeater.measure_task(cur_task, default_point=default_result[0])
            new_feature, new_label = split_features_and_labels(results, task["params"]["ResultFeatLabels"])
            features += new_feature
            labels += new_label
            if len(features) > len(search_space):
                print("Unable to finish normally, terminating with best results")
                min_en = min(labels)
                min_en_config = features[labels.index(min_en)]
                print("Measured best config: %s, energy: %s" % (str(min_en_config), str(min_en)))
                break
        #stop new file

    predicted_energy, predicted_point = reg.solution_labels, reg.solution_features
    print("\n\nPredicted energy: %s, with configuration: %s" % (predicted_energy[0], predicted_point))
    print("Number of measured points: %s" % len(features))
    print("Number of performed measurements: %s" % repeater.performed_measurements)
    print("Measured energy is: %s" % str(measured_energy[0]))


if __name__ == "__main__":
    run()
