__doc__ = """
Main module for running BRISE configuration balancing."""

import itertools
from logger.default_logger import Logger
from warnings import filterwarnings

from WSClient import WSClient
from model.model_selection import get_model
from repeater.repeater_selection import get_repeater
from tools.initial_config import initialize_config
from tools.features_tools import split_features_and_labels
from selection.selection_algorithms import get_selector

#####
import socket
# def client_connection():
#     IP = '0.0.0.0'
#     PORT = 9090
#     address = (IP, PORT)
#     socket_client = socket.socket()
#     socket_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     socket_client.connect(address)
#     return socket_client

# def client_stop_connection(socket_client):
#     socket_client.close()

IP = '0.0.0.0'
PORT = 9090
address = (IP, PORT)
socket_client = socket.socket()
socket_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
socket_client.connect(address)
#####


def run(APPI_QUEUE=None):

    # address = (IP, PORT)
    # socket_client = socket.socket()
    # socket_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # socket_client.connect(address)


    global_config, task_config = initialize_config()
    # Generate whole search space for regression.
    search_space = list(itertools.product(*task_config["DomainDescription"]["AllConfigurations"]))

    if APPI_QUEUE:
        APPI_QUEUE.put({"global_contig": global_config, "task": task_config})

    # Creating instance of selector based on selection type and
    # task data for further uniformly distributed data points generation.
    selector = get_selector(selection_algorithm_config=task_config["SelectionAlgorithm"],
                            search_space=task_config["DomainDescription"]["AllConfigurations"])

    # Instantiate client for Worker Service, establish connection.
    WS = WSClient(task_config=task_config,
                  ws_addr=global_config["WorkerService"]["Address"],
                  logfile='%s%s_WSClient.csv' % (global_config['results_storage'], task_config["ExperimentsConfiguration"]["FileToRead"]))

    # Creating runner for experiments that will repeat task running for avoiding fluctuations.
    repeater = get_repeater("default", WS)

    print("Measuring default configuration that we will used in regression to evaluate solution... ")
    default_result = repeater.measure_task([task_config["default_point"]], socket_client) #change it to switch inside and devide to
    default_features, default_value = split_features_and_labels(default_result, task_config["params"]["ResultFeatLabels"])
    print(default_value)

    if APPI_QUEUE:
        APPI_QUEUE.put({"default configuration": {'configuration': default_features, "result": default_value}})

    print("Measuring initial number experiments, while it is no sense in trying to create model"
          "\n(because there is no data)...")
    initial_task = [selector.get_next_point() for x in range(task_config["SelectionAlgorithm"]["NumberOfInitialExperiments"])]
    repeater = get_repeater(repeater_type=task_config["ExperimentsConfiguration"]["RepeaterDecisionFunction"], WS=WS)
    results = repeater.measure_task(initial_task, socket_client, default_point=default_result[0])
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

        model_built = model.build_model(socket_client, score_min=task_config["ModelCreation"]["MinimumAccuracy"])

        if model_built:
            model_validated = model.validate_model(search_space=search_space)

            if model_validated:
                predicted_labels, predicted_features = model.predict_solution(search_space=search_space)
                print("Predicted solution features:%s, labels:%s." %(str(predicted_features), str(predicted_labels)))
                validated_labels, finish = model.validate_solution(socket_client, task_config=task_config["ModelCreation"],
                                                                   repeater=repeater,
                                                                   default_value=default_value,
                                                                   predicted_features=predicted_features)

                features += predicted_features
                labels += validated_labels

                if finish:
                    optimal_result, optimal_config = model.get_result(repeater, features, labels)
                    return optimal_result, optimal_config

                else:
                    continue

        print("New data point needed to continue process of balancing. "
              "Number of data points retrieved from the selection algorithm: %s" % str(selector.numOfGeneratedPoints))
        print('='*120)
        cur_task = [selector.get_next_point() for x in range(task_config["SelectionAlgorithm"]["Step"])]

        # TODO: Discuss following commented step, because its domain - specific.
        # if self.solution_features:
        #     cur_task.append(self.solution_features)
        results = repeater.measure_task(cur_task, default_point=default_result[0])
        new_feature, new_label = split_features_and_labels(results, task_config["ModelCreation"]["FeaturesLabelsStructure"])
        features += new_feature
        labels += new_label

        # If BRISE cannot finish his work properly - terminate it.
        if len(features) > len(search_space):
            print("Unable to finish normally, terminating with best of measured results.")
            model.solution_labels = min(labels)
            model.solution_features = features[labels.index(model.solution_labels)]
            print("Measured best config: %s, energy: %s" % (str(model.solution_features), str(model.solution_labels)))
            optimal_result, optimal_config = model.get_result(repeater, features, labels)
            return optimal_result, optimal_config

if __name__ == "__main__":
    filterwarnings("ignore")    # disable warnings for demonstration.
    run()
