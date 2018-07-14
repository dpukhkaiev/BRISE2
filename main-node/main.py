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


def run(APPI_QUEUE=None):

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

    print("Measuring default configuration that we will used in regression to evaluate solution... ", end='')
    default_result = repeater.measure_task([task_config["DomainDescription"]["DefaultConfiguration"]]) #change it to switch inside and devide to
    default_features, default_value = split_features_and_labels(default_result, task_config["ModelCreation"]["FeaturesLabelsStructure"])
    print(default_value)

    if APPI_QUEUE:
        APPI_QUEUE.put({"default configuration": {'configuration': default_features, "result": default_value}})

    print("Measuring initial number experiments, while it is no sense in trying to create model"
          "\n(because there is no data)...")
    initial_task = [selector.get_next_point() for x in range(task_config["SelectionAlgorithm"]["NumberOfInitialExperiments"])]
    repeater = get_repeater(repeater_type=task_config["ExperimentsConfiguration"]["RepeaterDecisionFunction"], WS=WS)
    results = repeater.measure_task(initial_task, default_point=default_result[0])
    features, labels = split_features_and_labels(results, task_config["ModelCreation"]["FeaturesLabelsStructure"])
    print("Results got. Building model..")

    # The main effort does here.
    # First - Building model.
    # Second - Verification of model.
    # Third a - If all is OK - prediction of best configuration and verification it by measuring.
    # Third b - If model have not been build - continue making predictions using selector and performing experiments.
    # Fourth a - Go to First (as new data was already measured in Third a).
    # Fourth b - Make new prediction and experiment,  go to First.
    # Fifth - Report results.
    #
    finish = False
    while not finish:
        model = get_model(model_creation_config=task_config["ModelCreation"],
                          log_file_name="%s%s%s_model.txt" % (global_config['results_storage'],
                                                              task_config["ExperimentsConfiguration"]["FileToRead"],
                                                              task_config["ModelCreation"]["ModelType"]),
                          features=features,
                          labels=labels)

        successfully_built_model = model.build_model(score_min=0.85,
                                                     searchspace=search_space)

        if not successfully_built_model:
            print("New data point needed to continue building model. Current number of data points: %s" % str(selector.numOfGeneratedPoints))
            print('='*100)
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
                finish = True

        elif successfully_built_model:
            predicted_features, predicted_labels, prediction_is_final = model.predict_and_validate(task_config["ModelCreation"], repeater, default_value)
            features += predicted_features
            labels += predicted_labels
            if prediction_is_final:
                finish = True

    optimal_result, optimal_config = model.get_result(repeater, features, labels)

if __name__ == "__main__":
    filterwarnings("ignore")    # disable warnings for demonstration.
    run()
