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
from selection.selection_algorithms import get_selector
from logger.default_logger import BRISELogConfigurator
from stop_condition.stop_condition_selection import get_stop_condition

from core_entities.experiment import Experiment


def run(io=None):
    time_started = datetime.datetime.now()

    if __name__ == "__main__":
        logger = BRISELogConfigurator().get_logger(__name__)
    else:
        logger = logging.getLogger(__name__)
    logger.info("Starting BRISE...")
    if not io:
        logger.warning("Running BRISE without provided API object.")
    # argv is a run parameters for main - using for configuration
    experiment = Experiment()
    global_config, experiment.description = initialize_config(argv)

    # Generate whole search space for model.
    experiment.search_space = [list(tup) for tup in itertools.product(*experiment.description["DomainDescription"]["AllConfigurations"])]

    if io:
        # APPI_QUEUE.put({"global_config": global_config, "task": experiment.description})
        temp = {"global_config": global_config, "task": experiment.description}
        io.emit('main_config', temp)
        logger.debug("Task configuration and global configuration are sent to the API.")

    # Creating instance of selector based on selection type and
    # task data for further uniformly distributed data points generation.
    selector = get_selector(experiment=experiment)

    # Instantiate client for Worker Service, establish connection.
    WS = WSClient(experiment.description["ExperimentsConfiguration"], global_config["WorkerService"]["Address"],
                  logfile='%s%s_WSClient.csv' % (global_config['results_storage'],
                                                 experiment.description["ExperimentsConfiguration"]["WorkerConfiguration"]["ws_file"]))

    # Creating runner for experiments that will repeat task running for avoiding fluctuations.
    repeater = get_repeater("default", WS, experiment)

    logger.info("Measuring default configuration that we will used in regression to evaluate solution... ")
    default_features = [experiment.description["DomainDescription"]["DefaultConfiguration"]]
    default_configurations = repeater.measure_task(experiment, default_features, io)
    # default_result = repeater.measure_task(experiment, default_features, io)
    # default_value = default_result
    logger.info("Results of measuring default value: %s" % default_configurations[0].average_result)

    if io:
        # TODO An array in the array with one value.
        # Events 'default conf' and 'task result' must be similar
        temp = {
            "configuration": repeater.point_to_dictionary(default_features[0]),
            "result": default_configurations[0].average_result
        }
        io.emit("default conf", temp)

    logger.info("Measuring initial number experiments, while it is no sense in trying to create model"
                "\n(because there is no data)...")
    initial_task = [selector.get_next_point() for x in range(experiment.description["SelectionAlgorithm"]["NumberOfInitialExperiments"])]
    repeater = change_decision_function(repeater, experiment.description["ExperimentsConfiguration"]["RepeaterDecisionFunction"])
    results_configurations = repeater.measure_task(experiment, initial_task, io, default_point=default_configurations[0].average_result)
    # features = initial_task
    # labels = results
    logger.info("Results got. Building model..")

    model = get_model(experiment=experiment,
                      log_file_name="%s%s%s_model.txt" % (global_config['results_storage'],
                                                          experiment.description["ExperimentsConfiguration"]["WorkerConfiguration"]["ws_file"],
                                                          experiment.description["ModelConfiguration"]["ModelType"]))

    # The main effort does here.
    # 1. Building model.
    # 2. If model built - validation of model.
    # 3. If model is valid - prediction solution and verification it by measuring.
    # 4. If solution is OK - reporting and terminating. If not - add it to all data set and go to 1.
    # 5. Get new point from selection algorithm, measure it, check if termination needed and go to 1.
    #

    stop_condition = get_stop_condition(experiment=experiment)

    finish = False
    cur_stats_message = "\nNew data point needed to continue process of balancing. " \
                        "%s configuration points of %s was evaluated. %s retrieved from the selection algorithm.\n" \
                        + '='*120
    configurations = experiment.all_configurations

    while not finish:
        model.add_data(configurations)
        model_built = model.build_model()

        if model_built:
            model_validated = model.validate_model(io=io, search_space=experiment.search_space)

            if model_validated:
                predicted_labels, predicted_features = model.predict_solution(io=io, search_space=experiment.search_space)
                logger.info("Predicted solution features:%s, labels:%s." % (str(predicted_features),
                                                                            str(predicted_labels)))

                if io:
                    io.emit('info', {'message': "Verifying solution that model gave.."})

                # "repeater.measure_task" works with list of tasks. "predicted_features" is one task,
                # because of that it is transmitted as list
                solution_candidate_configurations = repeater.measure_task(experiment=experiment, task=[predicted_features], io=io)
                configurations, finish = stop_condition.validate_solution(
                                                   solution_candidate_configurations=solution_candidate_configurations,
                                                   current_best_configurations=default_configurations)

                model.solution_configuration = configurations
                model.solution_labels = configurations[0].average_result
                model.solution_features = configurations[0].configuration

                selector.disable_point(predicted_features)

                if finish:
                    if io:
                        io.emit('info', {'message': "Solution validation success!"})
                    model.add_data(configurations)
                    optimal_result, optimal_config = model.get_result(repeater, io=io)
                    write_results(global_config, experiment.description, time_started, configurations,
                                  repeater.performed_measurements, optimal_config, optimal_result, default_configurations)
                    return optimal_result, optimal_config

                else:
                    logger.info(cur_stats_message
                                % (len(model.all_features), len(experiment.search_space), str(selector.numOfGeneratedPoints)))
                    continue

        logger.info(cur_stats_message % (len(model.all_features), len(experiment.search_space), str(selector.numOfGeneratedPoints)))
        cur_task = [selector.get_next_point() for x in range(experiment.description["SelectionAlgorithm"]["Step"])]

        results = repeater.measure_task(experiment, cur_task, io=io, default_point=default_configurations[0].average_result)
        features = cur_task
        labels = results

        # If BRISE cannot finish his work properly - terminate it.
        if len(model.all_features) > len(experiment.search_space):
            logger.info("Unable to finish normally, terminating with best of measured results.")
            model.add_data(features, labels)
            optimal_result, optimal_config = model.get_result(repeater, io=io)
            write_results(global_config, experiment.description, time_started, configurations,
                          repeater.performed_measurements, optimal_config, optimal_result, default_configurations)
            return optimal_result, optimal_config


if __name__ == "__main__":
    run()
