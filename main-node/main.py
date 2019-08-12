__doc__ = """
Main module for running BRISE configuration balancing."""

import logging

from warnings import filterwarnings
filterwarnings("ignore")    # disable warnings for demonstration.

from WorkerServiceClient.WSClient_sockets import WSClient
from model.model_selection import get_model
from repeater.repeater import Repeater
from tools.initial_config import load_global_config, load_experiment_description, validate_experiment_description
from tools.front_API import API
from selection.selection_algorithms import get_selector
from logger.default_logger import BRISELogConfigurator
from stop_condition.stop_condition_selector import get_stop_condition
from core_entities.experiment import Experiment
from core_entities.configuration import Configuration


def run(experiment_description=None):
    try:
        sub = API() # subscribers

        if __name__ == "__main__":
            logger = BRISELogConfigurator().get_logger(__name__)
        else:
            logger = logging.getLogger(__name__)
        logger.info("Starting BRISE")
        sub.send('log', 'info', message="Starting BRISE")
        global_config = load_global_config()

        if not experiment_description:
            logger.warning("Experiment Description was not provided by the API, using the default one.")
            experiment_description = load_experiment_description()
        validate_experiment_description(experiment_description)

        experiment = Experiment(experiment_description)
        Configuration.set_task_config(experiment.description["TaskConfiguration"])

        sub.send('experiment', 'description', global_config=global_config, experiment_description=experiment.description)
        logger.debug("Experiment description and global configuration sent to the API.")

        # Creating instance of selector algorithm, according to specified in experiment description type.
        selector = get_selector(experiment=experiment)

        # Instantiate client for Worker Service, establish connection.

        worker_service_client = WSClient(experiment.description["TaskConfiguration"], global_config["WorkerService"]["Address"],
                                         logfile='%s%s_WSClient.csv' % (global_config['results_storage'],
                                                                        experiment.get_name()))

        # Creating runner for experiments that will repeat the configuration measurement to avoid fluctuations.
        repeater = Repeater(worker_service_client, experiment)

        temp_msg = "Measuring the default Configuration."
        logger.info(temp_msg)
        sub.send('log', 'info', message=temp_msg)

        default_configuration = Configuration(experiment.description["DomainDescription"]["DefaultConfiguration"])
        repeater.measure_configurations([default_configuration], experiment=experiment)
        experiment.put_default_configuration(default_configuration)

        selector.disable_configurations([default_configuration])

        temp_msg = "Running initial configurations, while there is no sense in trying to create the model without a data..."
        logger.info(temp_msg)
        sub.send('log', 'info', message=temp_msg)

        initial_configurations = [Configuration(selector.get_next_configuration()) for _ in
                                  range(experiment.description["SelectionAlgorithm"]["NumberOfInitialConfigurations"])]

        repeater.set_type(experiment.description["Repeater"]["Type"])
        repeater.measure_configurations(initial_configurations, experiment=experiment)
        experiment.add_configurations(initial_configurations)

        logger.info("Results got. Building model..")
        sub.send('log', 'info', message="Results got. Building model..")

        model = get_model(experiment=experiment,
                          log_file_name="%s%s%s_model.txt" % (global_config['results_storage'],
                                                              experiment.get_name(),
                                                              experiment.description["ModelConfiguration"]["ModelType"]))

        # The main effort does here.
        # 1. Building model.
        # 2. If model built - validation of model.
        # 3. If model is valid - prediction and evaluation of current solution Configuration, else - go to 5.
        # 4. Evaluation of Stop Condition, afterwards - terminating or going to 5.
        # 5. Get new point from selection algorithm, measure it, check if termination needed and go to 1.

        stop_condition = get_stop_condition(experiment)

        finish = False
        cur_stats_message = "-- New Configuration(s) was(were) measured. Currently were evaluated %s of %s Configurations. " \
                            "%s of them out of the Selection Algorithm. Building Target System model.\n"

        while not finish:
            model_built = model.update_data(experiment.all_configurations).build_model()
            number_of_configurations_in_iteration = experiment.get_number_of_configurations_per_iteration() \
                        if experiment.get_number_of_configurations_per_iteration() \
                            else repeater.worker_service_client.get_number_of_workers()
            stop_condition.update_number_of_configurations_in_iteration(number_of_configurations_in_iteration)

            if model_built and model.validate_model():
                predicted_configurations = model.predict_next_configurations(number_of_configurations_in_iteration)
                temp_msg = "Predicted following Configuration->Quality pairs: %s" \
                           % list((str(c.get_parameters()) + "->" + str(c.predicted_result) for c in predicted_configurations))
                logger.info(temp_msg)
                sub.send('log', 'info', message=temp_msg)
                repeater.measure_configurations(predicted_configurations, experiment=experiment)
                experiment.add_configurations(predicted_configurations)
                selector.disable_configurations(predicted_configurations)
            else:
                configs_from_selector = [Configuration(selector.get_next_configuration()) for _ in
                                         range(number_of_configurations_in_iteration)]

                repeater.measure_configurations(configs_from_selector, experiment=experiment)
                experiment.add_configurations(configs_from_selector)

            finish = stop_condition.validate_conditions()
            if finish:
                optimal_configuration = experiment.get_final_report_and_result(repeater)
                return optimal_configuration
            else:
                temp_msg = cur_stats_message % (len(model.all_configurations), len(experiment.search_space),
                                                str(selector.numOfGeneratedPoints))
                logger.info(temp_msg)
                sub.send('log', 'info', message=temp_msg)
                continue

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error("BRISE was terminated by Exception: %s." % type(e), exc_info=e)
        if 'experiment' in dir() and 'repeater' in dir():
            logger.info("Reporting currently best found Configuration.")
            try:
                return experiment.get_final_report_and_result(repeater)
            except Exception as e:
                logger.error("Unable to retrieve currently best found Configuration.", exc_info=e)
    finally:
        worker_service_client.disconnect()


if __name__ == "__main__":
    run()
