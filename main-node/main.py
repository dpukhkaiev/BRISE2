__doc__ = """
Main module for running benchmark 

Requirements: 
    -   sklearn(with all deps like numpy, scipy : 0.19.1   
    -   sobol_seq
    -   
"""

from WSClient import WSClient
from model.model_selection import get_model
from repeater.repeater_selection import get_repeater
from tools.initial_config import initialize_config
from tools.features_tools import split_features_and_labels
from selection.selection_algorithms import get_selector
from logger.default_logger import Logger

import urllib.parse
import json
import numpy
import itertools

# disable warnings for demonstration.
from warnings import filterwarnings
filterwarnings("ignore")


def run():

    globalConfig, task = initialize_config()

    # logger = create_logger(name_of_logger=__name__, global_config=globalConfig)
    # logger.info("")

    # Creating instance of selector based on selection type and task data for further uniformly distributed data points generation.
    selector = get_selector(selector_type=task["params"]["SelectionType"],
                            data=task["TaskDataPoints"])
    #   Connect to the Worker Service and send task.
    WS = WSClient(task_name=task["task_name"],
                  task_params=task["params"],
                  ws_addr=globalConfig["WorkerService"]["Address"],
                  logfile='%s%s_WSClient.csv' % (globalConfig['results_storage'], task['params']["FileToRead"]))

    # Creating runner for experiments that will repeat task running for avoiding fluctuations.
    repeater = get_repeater("default", WS)

    # Need to find default value that we will used in regression to evaluate solution
    print("Getting default value..") 
    
    default_result = repeater.measure_task([task["default_point"]]) #change it to switch inside and devide to
    default_features, default_value = split_features_and_labels(default_result, task["params"]["ResultFeatLabels"])
    print(default_value)

    # Creating initial set of points for testing and first attempt to create regression model.
    initial_task = [selector.get_next_point() for x in range(task["params"]["NumberOfInitialExperiments"])]

    # Results will be in a list of points, each point is also a list of values:
    # [[val1, val2,... valN], [val1, val2,... valN]...]
    print("Sending initial task..")
    repeater = get_repeater(task["params"]["DecisionFunction"], WS)
    results = repeater.measure_task(initial_task, default_point=default_result[0])
    print("Results got, splitting to features and labels..")
    features, labels = split_features_and_labels(results, task["params"]["ResultFeatLabels"])

    # Generate whole search space for regression.
    search_space = list(itertools.product(*task["TaskDataPoints"]))

    success = False
    while not success:
        model = get_model(model_type=task["params"]["ModelType"], 
                          res_storage=globalConfig['results_storage'], 
                          file_to_read=task['params']["FileToRead"], 
                          model_test_size=task["params"]["ModelTestSize"], 
                          features=features, 
                          labels=labels)

        success = model.build_model(param=task["params"],
                                    score_min=0.85,
                                    searchspace=search_space)
        features, labels, real_result, success = model.validate(success, task, repeater, selector, default_value, default_result, search_space, features, labels)

    optimal_result, optimal_config = model.get_result(features, repeater, real_result) 


if __name__ == "__main__":
    run()
