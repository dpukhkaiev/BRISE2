__doc__ = """
Main module for running BRISE configuration balancing."""

import itertools
from sys import argv
import logging

from warnings import filterwarnings
filterwarnings("ignore")    # disable warnings for demonstration.

from WorkerServiceClient.WSClient_sockets import WSClient
from model.model_selection import get_model
from repeater.repeater import Repeater
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

    # Generate whole search space for model.
    experiment.search_space = [list(configuration) for configuration in itertools.product(*experiment.description["DomainDescription"]["AllConfigurations"])]

    sub.send('experiment', 'description', global_config=global_config, experiment_description=experiment.description)
    logger.debug("Experiment description and global configuration sent to the API.")

    # Creating instance of selector algorithm, according to specified in experiment description type.
    selector = get_selector(experiment=experiment)

    # Instantiate client for Worker Service, establish connection.
    # TODO: LOGFILE parameter should be chosen according to the name of file, that provides Experiment description
    # (task.json)

    worker_service_client = WSClient(experiment.description["TaskConfiguration"], global_config["WorkerService"]["Address"],
                                     logfile='%s%s_WSClient.csv' % (global_config['results_storage'],
                                                                    experiment.description["TaskConfiguration"]
                                                                    ["WorkerConfiguration"]["ws_file"]))

    # Creating runner for experiments that will repeat the configuration measurement to avoid fluctuations.
    repeater = Repeater(worker_service_client, experiment)

    temp_msg = "Measuring default configuration that we will used in regression to evaluate solution."
    # TODO: Logging messages to the API could be sent from the logger.
    logger.info(temp_msg)
    sub.send('log', 'info', message=temp_msg)

    default_configuration = Configuration(experiment.description["DomainDescription"]["DefaultConfiguration"])
    repeater.measure_configurations([default_configuration], experiment=experiment)
    experiment.put_default_configuration(default_configuration)

    selector.disable_point(default_configuration.get_parameters())

    temp_msg = "Results of measuring default value: %s" % experiment.default_configuration.get_average_result()
    logger.info(temp_msg)
    sub.send('log', 'info', message=temp_msg)

    temp_msg = "Running initial configurations, while there is no sense in trying to create the model without a data..."
    logger.info(temp_msg)
    sub.send('log', 'info', message=temp_msg)

    initial_configurations = [Configuration(selector.get_next_point()) for _ in
                              range(experiment.description["SelectionAlgorithm"]["NumberOfInitialConfigurations"])]

    repeater.set_type(experiment.description["Repeater"]["Type"])
    repeater.measure_configurations(initial_configurations, experiment=experiment)
    experiment.add_configurations(initial_configurations)

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
    # 3. If model is valid - prediction and evaluation of current solution Configuration, else - go to 5.
    # 4. Evaluation of Stop Condition, afterwards - terminating or going to 5.
    # 5. Get new point from selection algorithm, measure it, check if termination needed and go to 1.

    stop_condition = get_stop_condition(experiment=experiment)

    finish = False
    cur_stats_message = "-- New Configuration(s) measured. Currently were evaluated %s of %s Configurations." \
                        "%s of them out of the Selection Algorithm. Building Target System model.\n"

    while not finish:
        model_built = model.update_data(experiment.all_configurations).build_model()
        if model_built:
            # TODO: move behavior for 'else' here (out of models)?
            if model.validate_model():
                # TODO: Need to agree on return structure (nested or not).
                predicted_configuration = model.predict_solution()
                selector.disable_point(predicted_configuration.get_parameters())
                temp_msg = "Predicted solution configuration: %s, Quality: %s." \
                           % (str(predicted_configuration.get_parameters()), str(predicted_configuration.predicted_result))
                logger.info(temp_msg)
                sub.send('log', 'info', message=temp_msg)
                repeater.measure_configurations([predicted_configuration], experiment=experiment)
                experiment.add_configurations([predicted_configuration])
                finish = stop_condition.validate_solution(solution_candidate_configurations=[predicted_configuration],
                                                          current_best_configurations=experiment.current_best_configurations)
                if finish:
                    sub.send('log', 'info', message="Solution validation success!")
                    optimal_configuration = experiment.get_final_report_and_result(repeater)
                    # TODO: Store global_config im Experiment?
                    write_results(global_config=global_config, experiment_current_status=experiment.get_current_status())
                    return optimal_configuration
                else:
                    temp_msg = cur_stats_message % (len(model.all_configurations), len(experiment.search_space),
                                                    str(selector.numOfGeneratedPoints))
                    logger.info(temp_msg)
                    sub.send('log', 'info', message=temp_msg)
                    continue

        configs_from_selector = [Configuration(selector.get_next_point()) for _ in
                                 range(experiment.description["SelectionAlgorithm"]["Step"])]

        repeater.measure_configurations(configs_from_selector, experiment=experiment)
        experiment.add_configurations(configs_from_selector)

        # If BRISE cannot finish his work properly - terminate it.
        if len(experiment.all_configurations) > len(experiment.search_space):
            # TODO: @Zhenya, Is it possible to replace this 'if' with following comment?
            #  finish = stop_condition.validate_solution(solution_candidate_configurations=configs_from_selector,
            #         current_best_configurations=experiment.current_best_configurations)
            logger.info("Unable to finish normally, terminating with best of measured results.")
            optimal_configuration = experiment.get_final_report_and_result(repeater)
            write_results(global_config=global_config, experiment_current_status=experiment.get_current_status())
            return optimal_configuration

        temp_msg = cur_stats_message % (len(model.all_configurations), len(experiment.search_space), str(selector.numOfGeneratedPoints))
        logger.info(temp_msg)
        sub.send('log', 'info', message=temp_msg)


if __name__ == "__main__":
    run()
