__doc__ = """
Main module for running BRISE configuration balancing."""

import itertools
import datetime
import socket
from sys import argv

from warnings import filterwarnings
filterwarnings("ignore")    # disable warnings for demonstration.

from WSClient import WSClient
from model.model_selection import get_model
from repeater.repeater_selection import get_repeater
from tools.initial_config import initialize_config
from tools.features_tools import split_features_and_labels
from tools.write_results import write_results
from selection.selection_algorithms import get_selector


def run(io=None):
    time_started = datetime.datetime.now()

    # argv is a run parameters for main - using for configuration
    global_config, task_config = initialize_config(argv)

    # Connect to socket server
    socket_client = client_connection(connection=global_config['frontend'])

    # Generate whole search space for regression.
    search_space = list(itertools.product(*task_config["DomainDescription"]["AllConfigurations"]))

    if io:
        # APPI_QUEUE.put({"global_config": global_config, "task": task_config})
        temp = {"global_config": global_config, "task": task_config}
        io.emit('main_config', temp)
        

    # Creating instance of selector based on selection type and
    # task data for further uniformly distributed data points generation.
    selector = get_selector(selection_algorithm_config=task_config["SelectionAlgorithm"],
                            search_space=task_config["DomainDescription"]["AllConfigurations"])

    # Instantiate client for Worker Service, establish connection.
    WS = WSClient(task_config=task_config,
                  ws_addr=global_config["WorkerService"]["Address"],
                  logfile='%s%s_WSClient.csv' % (global_config['results_storage'], task_config["ExperimentsConfiguration"]["FileToRead"]))

    # Creating runner for experiments that will repeat task running for avoiding fluctuations.
    repeater = get_repeater("default", WS, task_config["ExperimentsConfiguration"])

    print("Measuring default configuration that we will used in regression to evaluate solution... ")
    default_result = repeater.measure_task([task_config["DomainDescription"]["DefaultConfiguration"]], io) #change it to switch inside and devide to
    default_features, default_value = split_features_and_labels(default_result, task_config["ModelCreation"]["FeaturesLabelsStructure"])
    print(default_value)

    if io:
        temp = {'conf': default_features, "result": default_value}
        io.emit('default conf', temp)
        # APPI_QUEUE.put({"default configuration": {'configuration': default_features, "result": default_value}})

    print("Measuring initial number experiments, while it is no sense in trying to create model"
          "\n(because there is no data)...")
    initial_task = [selector.get_next_point() for x in range(task_config["SelectionAlgorithm"]["NumberOfInitialExperiments"])]
    repeater = get_repeater(repeater_type=task_config["ExperimentsConfiguration"]["RepeaterDecisionFunction"],
                            WS=WS, experiments_configuration=task_config["ExperimentsConfiguration"])
    results = repeater.measure_task(initial_task, io, default_point=default_result[0])
    features, labels = split_features_and_labels(results, task_config["ModelCreation"]["FeaturesLabelsStructure"])
    print("Results got. Building model..")

    # The main effort does here.
    # 1. Loading and building model.
    # 2. If model built - validation of model.
    # 3. If model is valid - prediction solution and verification it by measuring.
    # 4. If solution is OK - reporting and terminating. If not - add it to all data set and go to 1.
    # 5. Get new point from selection algorithm, measure it, check if termination needed and go to 1.
    #
    finish = False
    while not finish:

        model = get_model(model_creation_config=task_config["ModelCreation"],
                          log_file_name="%s%s%s_model.txt" % (global_config['results_storage'],
                                                              task_config["ExperimentsConfiguration"]["FileToRead"],
                                                              task_config["ModelCreation"]["ModelType"]),
                          features=features,
                          labels=labels)

        model_built = model.build_model(score_min=task_config["ModelCreation"]["MinimumAccuracy"])

        if model_built:
            model_validated = model.validate_model(io=io, search_space=search_space)

            if model_validated:
                predicted_labels, predicted_features = model.predict_solution(io=io, search_space=search_space)
                print("Predicted solution features:%s, labels:%s." %(str(predicted_features), str(predicted_labels)))
                validated_labels, finish = model.validate_solution(io=io, task_config=task_config["ModelCreation"],
                                                                   repeater=repeater,
                                                                   default_value=default_value,
                                                                   predicted_features=predicted_features)

                features += [predicted_features]
                labels += [validated_labels]

                if finish:
                    optimal_result, optimal_config = model.get_result(repeater, features, labels, io=io)
                    write_results(global_config, task_config, time_started, features, labels,
                                  repeater.performed_measurements, optimal_config, optimal_result, default_features, default_value)
                    return optimal_result, optimal_config

                else:
                    continue

        print("New data point needed to continue process of balancing. "
              "Number of data points retrieved from the selection algorithm: %s" % str(selector.numOfGeneratedPoints))
        print('='*120)
        cur_task = [selector.get_next_point() for x in range(task_config["SelectionAlgorithm"]["Step"])]

        results = repeater.measure_task(cur_task, io=io, default_point=default_result[0])
        new_feature, new_label = split_features_and_labels(results, task_config["ModelCreation"]["FeaturesLabelsStructure"])
        features += new_feature
        labels += new_label

        # If BRISE cannot finish his work properly - terminate it.
        if len(features) > len(search_space):
            print("Unable to finish normally, terminating with best of measured results.")
            optimal_result, optimal_config = model.get_result(repeater, features, labels, io=io)
            write_results(global_config, task_config, time_started, features, labels,
                          repeater.performed_measurements, optimal_config, optimal_result, default_features,
                          default_value)
            return optimal_result, optimal_config


if __name__ == "__main__":
    run()
