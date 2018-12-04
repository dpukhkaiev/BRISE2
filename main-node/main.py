__doc__ = """
Main module for running BRISE configuration balancing."""

import itertools
import datetime
from sys import argv
import logging

from warnings import filterwarnings
filterwarnings("ignore")    # disable warnings for demonstration.

from WorkerServiceClient.WSClient_sockets import WSClient
from model.model_selection import get_model
from repeater.repeater_selection import get_repeater, change_decision_function
from tools.initial_config import initialize_config
from tools.write_results import write_results
from tools.front_API import API
from selection.selection_algorithms import get_selector
from logger.default_logger import BRISELogConfigurator


def run():
    time_started = datetime.datetime.now()
    sub = API() # subscribers
    print(sub)

    if __name__ == "__main__":
        logger = BRISELogConfigurator().get_logger(__name__)
    else:
        logger = logging.getLogger(__name__)

    logger.info("Starting BRISE")
    sub.send('log', 'info', message="Starting BRISE")
    if not sub:
        logger.warning("Running BRISE without provided API object.")
    # argv is a run parameters for main - using for configuration
    global_config, experiment_description = initialize_config(argv)

    # Generate whole search space for model.
    search_space = [list(configuration) for configuration in
                    itertools.product(*experiment_description["DomainDescription"]["AllConfigurations"])]

    sub.send('experiment', 'description', global_config=global_config, experiment_description=experiment_description)
    logger.debug("Experiment description and global configuration sent to the API.")

    # Creating instance of selector algorithm, according to specified in experiment description type.
    selector = get_selector(selection_algorithm_config=experiment_description["SelectionAlgorithm"],
                            search_space=experiment_description["DomainDescription"]["AllConfigurations"])

    # Instantiate client for Worker Service, establish connection.
    # TODO: LOGFILE parameter should be chosen according to the name of file, that provides Experiment description
    # (task.json)

    WS = WSClient(experiment_description["TaskConfiguration"], global_config["WorkerService"]["Address"],
                  logfile='%s%s_WSClient.csv' % (global_config['results_storage'],
                                                 experiment_description["TaskConfiguration"]["WorkerConfiguration"]["ws_file"]))

    # Creating runner for experiments that will repeat the configuration measurement to avoid fluctuations.
    repeater = get_repeater("default", WS, experiment_description)

    temp_msg = "Measuring default configuration that we will used in regression to evaluate solution"
    # TODO: Logging messages to the API could be sent from the logger.
    logger.info(temp_msg)
    sub.send('log', 'info', message=temp_msg)

    default_result = repeater.measure_configuration([experiment_description["DomainDescription"]["DefaultConfiguration"]]) #change it to switch inside and devide to
    default_features = [experiment_description["DomainDescription"]["DefaultConfiguration"]]
    default_value = default_result

    temp_msg = "Results of measuring default value: %s" % default_value
    logger.info(temp_msg)
    sub.send('log', 'info', message=temp_msg)

    # TODO An array in the array with one value.
    # Events 'default conf' and 'task result' must be similar
    sub.send('default', 'configuration', configurations=default_features, results=[default_value[0]])

    temp_msg = "Running initial configurations, while there is no sense in trying to create the model without a data..."
    logger.info(temp_msg)
    sub.send('log', 'info', message=temp_msg)

    features = [selector.get_next_point() for _ in
                range(experiment_description["SelectionAlgorithm"]["NumberOfInitialConfigurations"])]

    repeater = change_decision_function(repeater,
                                        experiment_description["TaskConfiguration"]["RepeaterDecisionFunction"])
    labels = repeater.measure_configuration(features, default_point=default_result[0])
    logger.info("Results got. Building model..")
    sub.send('log', 'info', message="Results got. Building model..")

    # TODO: LOGFILE parameter should be chosen according to the name of file, that provides Experiment description
    model = get_model(model_config=experiment_description["ModelConfiguration"],
                      log_file_name="%s%s%s_model.txt" % (global_config['results_storage'],
                                                          experiment_description["TaskConfiguration"]["WorkerConfiguration"]["ws_file"],
                                                          experiment_description["ModelConfiguration"]["ModelType"]),
                      experiment_description=experiment_description)

    # The main effort does here.
    # 1. Building model.
    # 2. If model built - validation of model.
    # 3. If model is valid - prediction solution and verification it by measuring.
    # 4. If solution is OK - reporting and terminating. If not - add it to all data set and go to 1.
    # 5. Get new point from selection algorithm, measure it, check if termination needed and go to 1.
    #
    finish = False
    cur_stats_message = "-- New configuration measurement is needed to proceed. " \
                        "%s configuration points of %s was evaluated. %s retrieved from the selection algorithm.\n"
    while not finish:
        model.add_data(features, labels)
        model_built = model.build_model()

        if model_built:
            model_validated = model.validate_model(search_space=search_space)

            if model_validated:
                predicted_labels, predicted_features = model.predict_solution(search_space=search_space)
                temp_msg = "Predicted solution features:%s, labels:%s." % (str(predicted_features), str(predicted_labels))
                logger.info(temp_msg)
                sub.send('log', 'info', message=temp_msg)
                validated_labels, finish = model.validate_solution(repeater=repeater,
                                                                   default_value=default_value,
                                                                   predicted_features=predicted_features)

                features = [predicted_features]
                labels = [validated_labels]
                selector.disable_point(predicted_features)

                if finish:
                    model.add_data(features, labels)
                    optimal_result, optimal_config = model.get_result(repeater)

                    write_results(global_config, experiment_description, time_started, features, labels,
                                  repeater.performed_measurements, optimal_config, optimal_result, default_features,
                                  default_value)

                    return optimal_result, optimal_config

                else:
                    temp_msg = cur_stats_message % (
                        len(model.all_features), len(search_space), str(selector.numOfGeneratedPoints))
                    logger.info(temp_msg)
                    # sub.send('log', 'info', message=temp_msg)
                    continue

        temp_msg = cur_stats_message % (len(model.all_features), len(search_space), str(selector.numOfGeneratedPoints))
        logger.info(temp_msg)
        sub.send('log', 'info', message=temp_msg)
        features = [selector.get_next_point() for _ in range(experiment_description["SelectionAlgorithm"]["Step"])]

        labels = repeater.measure_configuration(features, default_point=default_result[0])

        # If BRISE cannot finish his work properly - terminate it.
        if len(model.all_features) > len(search_space):
            logger.info("Unable to finish normally, terminating with best of measured results.")
            model.add_data(features, labels)
            optimal_result, optimal_config = model.get_result(repeater)
            write_results(global_config, experiment_description, time_started, features, labels,
                          repeater.performed_measurements, optimal_config, optimal_result, default_features,
                          default_value)
            return optimal_result, optimal_config


if __name__ == "__main__":
    run()
