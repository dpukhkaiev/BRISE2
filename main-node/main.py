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
from stop_condition.stop_condition_selection import get_stop_condition

from core_entities.experiment import Experiment
from core_entities.configuration import Configuration


def run():

    sub = API() # subscribers

    if __name__ == "__main__":
        logger = BRISELogConfigurator().get_logger(__name__)
    else:
        logger = logging.getLogger(__name__)

    logger.info("Starting BRISE")
    sub.send('log', 'info', message="Starting BRISE")
    # argv is a run parameters for main - using for configuration
    global_config, experiment_description = initialize_config(argv)
    experiment = Experiment(experiment_description)
    experiment.put_start_time(datetime.datetime.now())

    # Generate whole search space for model.
    experiment.search_space = [list(configuration) for configuration in itertools.product(*experiment.description["DomainDescription"]["AllConfigurations"])]


    sub.send('experiment', 'description', global_config=global_config, experiment_description=experiment.description)
    logger.debug("Experiment description and global configuration sent to the API.")

    # Creating instance of selector algorithm, according to specified in experiment description type.
    selector = get_selector(experiment=experiment)

    # Instantiate client for Worker Service, establish connection.
    # TODO: LOGFILE parameter should be chosen according to the name of file, that provides Experiment description
    # (task.json)

    WS = WSClient(experiment.description["TaskConfiguration"], global_config["WorkerService"]["Address"],
                  logfile='%s%s_WSClient.csv' % (global_config['results_storage'],
                                                 experiment.description["TaskConfiguration"]["WorkerConfiguration"]["ws_file"]))

    # Creating runner for experiments that will repeat the configuration measurement to avoid fluctuations.
    repeater = get_repeater("default", WS, experiment)

    temp_msg = "Measuring default configuration that we will used in regression to evaluate solution."
    # TODO: Logging messages to the API could be sent from the logger.
    logger.info(temp_msg)
    sub.send('log', 'info', message=temp_msg)

    default_configuration = Configuration(experiment.description["DomainDescription"]["DefaultConfiguration"])
    experiment.put_default_configuration([default_configuration])
    repeater.measure_configuration(experiment, experiment.default_configuration)
    experiment.put(configuration_instance=default_configuration)

    selector.disable_point(default_configuration.get_parameters())

    temp_msg = "Results of measuring default value: %s" % experiment.default_configuration[0].get_average_result()
    logger.info(temp_msg)
    sub.send('log', 'info', message=temp_msg)

    # TODO An array in the array with one value.
    # Events 'default conf' and 'task result' must be similar
    sub.send('default', 'configuration', configurations=[experiment.default_configuration[0].get_parameters()],
             results=[experiment.default_configuration[0].get_average_result()])

    temp_msg = "Running initial configurations, while there is no sense in trying to create the model without a data..."
    logger.info(temp_msg)
    sub.send('log', 'info', message=temp_msg)

    initial_configurations = []
    for counter in range(experiment.description["SelectionAlgorithm"]["NumberOfInitialConfigurations"]):
        configuration = Configuration(selector.get_next_point())
        initial_configurations.append(configuration)

    repeater = change_decision_function(repeater, experiment.description["TaskConfiguration"]["RepeaterDecisionFunction"])
    repeater.measure_configuration(experiment, initial_configurations,
                                   default_point=experiment.default_configuration[0].get_average_result())
    for config in initial_configurations:
        experiment.put(configuration_instance=config)

    logger.info("Results got. Building model..")
    sub.send('log', 'info', message="Results got. Building model..")

    # TODO: LOGFILE parameter should be chosen according to the name of file, that provides Experiment description
    model = get_model(experiment=experiment,
                      log_file_name="%s%s%s_model.txt" % (global_config['results_storage'],
                                                          experiment.description["TaskConfiguration"]["WorkerConfiguration"]["ws_file"],
                                                          experiment.description["ModelConfiguration"]["ModelType"]))

    # The main effort does here.
    # 1. Building model.
    # 2. If model built - validation of model.
    # 3. If model is valid - prediction solution and verification it by measuring.
    # 4. If solution is OK - reporting and terminating. If not - add it to all data set and go to 1.
    # 5. Get new point from selection algorithm, measure it, check if termination needed and go to 1.

    stop_condition = get_stop_condition(experiment=experiment)

    finish = False
    cur_stats_message = "-- New configuration measurement is needed to proceed. " \
                        "%s configuration points of %s was evaluated. %s retrieved from the selection algorithm.\n"
    while not finish:
        model.add_data(experiment.all_configurations)
        model_built = model.build_model()
        predicted_configuration = None

        if model_built:
            model_validated = model.validate_model()

            if model_validated:
                # TODO: Need to agree on return structure (nested or not).
                predicted_configuration = model.predict_solution()


                temp_msg = "Predicted solution configuration: %s, Quality: %s." \
                           % (str(predicted_configuration.get_parameters()), str(predicted_configuration.predicted_result))
                logger.info(temp_msg)
                sub.send('log', 'info', message=temp_msg)
                repeater.measure_configuration(experiment=experiment, configurations=[predicted_configuration])
                experiment.put(predicted_configuration)
                finish = stop_condition.validate_solution(solution_candidate_configurations=[predicted_configuration],
                                                          current_best_configurations=experiment.default_configuration)
                model.solution_configuration = [predicted_configuration]
                selector.disable_point(predicted_configuration.get_parameters())

                if finish:
                    sub.send('log', 'info', message="Solution validation success!")
                    model.add_data(experiment.all_configurations)
                    optimal_configuration = experiment.get_final_report_and_result(model, repeater)
                    write_results(global_config=global_config, experiment_current_status=experiment.get_current_status())
                    return optimal_configuration

                else:
                    temp_msg = cur_stats_message % (len(model.all_configurations), len(experiment.search_space),
                                                    str(selector.numOfGeneratedPoints))
                    logger.info(temp_msg)
                    sub.send('log', 'info', message=temp_msg)
                    continue

        temp_msg = cur_stats_message % (len(model.all_configurations), len(experiment.search_space), str(selector.numOfGeneratedPoints))

        logger.info(temp_msg)
        sub.send('log', 'info', message=temp_msg)

        current_configurations_for_measuring = [] # list of Configuration instances
        for counter in range(experiment.description["SelectionAlgorithm"]["Step"]):
            configuration = Configuration(selector.get_next_point())
            current_configurations_for_measuring.append(configuration)

        repeater.measure_configuration(experiment=experiment, configurations=current_configurations_for_measuring,
                              default_point=experiment.default_configuration[0].get_average_result())
        for config in current_configurations_for_measuring:
            experiment.put(configuration_instance=config)

        # If BRISE cannot finish his work properly - terminate it.
        if len(experiment.all_configurations) > len(experiment.search_space):
            logger.info("Unable to finish normally, terminating with best of measured results.")
            model.add_data(configurations=experiment.all_configurations)
            optimal_configuration = experiment.get_final_report_and_result(model, repeater)
            write_results(global_config=global_config, experiment_current_status=experiment.get_current_status())
            return optimal_configuration


if __name__ == "__main__":
    run()
