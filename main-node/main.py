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
from core_entities.configuration import Configuration


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
    default_configuration = Configuration(experiment.description["DomainDescription"]["DefaultConfiguration"])
    repeater.measure_task(experiment, [default_configuration], io)
    logger.info("Results of measuring default value: %s" % default_configuration.average_result)
    selector.disable_point(default_configuration.configuration)

    if io:
        # TODO An array in the array with one value.
        # Events 'default conf' and 'task result' must be similar
        temp = {
            "configuration": repeater.point_to_dictionary(experiment.description["DomainDescription"]["DefaultConfiguration"]),
            "result": default_configuration.average_result
        }
        io.emit("default conf", temp)

    logger.info("Measuring initial number experiments, while it is no sense in trying to create model"
                "\n(because there is no data)...")

    initial_configurations = []
    for counter in range(experiment.description["SelectionAlgorithm"]["NumberOfInitialExperiments"]):
        configuration = Configuration(selector.get_next_point())
        initial_configurations.append(configuration)

    repeater = change_decision_function(repeater, experiment.description["ExperimentsConfiguration"]["RepeaterDecisionFunction"])
    repeater.measure_task(experiment, initial_configurations, io, default_point=default_configuration.average_result)
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

    stop_condition = get_stop_condition(experiment=experiment)

    finish = False
    cur_stats_message = "\nNew data point needed to continue process of balancing. " \
                        "%s configuration points of %s was evaluated. %s retrieved from the selection algorithm.\n" \
                        + '='*120

    while not finish:
        model.add_data(experiment.all_configurations)
        model_built = model.build_model()
        predicted_configuration = None

        if model_built:
            model_validated = model.validate_model(io=io, search_space=experiment.search_space)

            if model_validated:
                predicted_configuration = model.predict_solution(io=io)
                experiment.put(predicted_configuration)

                logger.info("Predicted solution features:%s, labels:%s." % (str(predicted_configuration.configuration),
                                                                            str(predicted_configuration.predicted_result)))

                if io:
                    io.emit('info', {'message': "Verifying solution that model gave.."})

                # "repeater.measure_task" works with list of tasks. "predicted_features" is one task,
                # because of that it is transmitted as list
                repeater.measure_task(experiment=experiment, configurations=[predicted_configuration], io=io)
                finish = stop_condition.validate_solution(solution_candidate_configurations=predicted_configuration,
                                                          current_best_configurations=default_configuration)

                model.solution_configuration = [predicted_configuration]

                selector.disable_point(predicted_configuration.configuration)

                if finish:
                    if io:
                        io.emit('info', {'message': "Solution validation success!"})
                    model.add_data(experiment.all_configurations)
                    optimal_configuration = model.get_result(repeater, io=io)
                    write_results(global_config=global_config, experiment_description=experiment.description,
                                  time_started=time_started, configurations=[predicted_configuration],
                                  performed_measurements=repeater.performed_measurements,
                                  optimal_configuration=optimal_configuration,
                                  default_configurations=[default_configuration])
                    return optimal_configuration

                else:
                    logger.info(cur_stats_message % (len(model.all_configurations), len(experiment.search_space),
                                                     str(selector.numOfGeneratedPoints)))
                    continue

        logger.info(cur_stats_message % (len(model.all_configurations), len(experiment.search_space), str(selector.numOfGeneratedPoints)))

        cur_task = []
        for counter in range(experiment.description["SelectionAlgorithm"]["Step"]):
            configuration = Configuration(selector.get_next_point())
            cur_task.append(configuration)

        repeater.measure_task(experiment=experiment, configurations=cur_task, io=io,
                              default_point=default_configuration.average_result)

        # If BRISE cannot finish his work properly - terminate it.
        if len(experiment.all_configurations) > len(experiment.search_space):
            logger.info("Unable to finish normally, terminating with best of measured results.")
            model.add_data(configurations=cur_task)
            optimal_configuration = model.get_result(repeater, io=io)
            write_results(global_config=global_config, experiment_description=experiment.description,
                          time_started=time_started, configurations=[predicted_configuration],
                          performed_measurements=repeater.performed_measurements,
                          optimal_configuration=optimal_configuration, default_configurations=[default_configuration])
            return optimal_configuration


if __name__ == "__main__":
    run()
