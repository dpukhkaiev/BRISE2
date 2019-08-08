__doc__ = """
Writing results of BRISE run to the output file."""

import datetime
import itertools
import logging

from tools.file_system_io import create_folder_if_not_exists


def write_results(global_config, experiment_current_status):
                  # experiment_description, time_started, configurations,
                  # performed_measurements, optimal_configuration, default_configurations):

    logger = logging.getLogger(__name__)
    create_folder_if_not_exists(global_config["results_storage"])

    # TODO: LOGFILE parameter should be chosen according to the name of file, that provides Experiment description
    file_path = "%sBRISE_Results_for_%s.txt" % (global_config["results_storage"],
                                                experiment_current_status["name"])
    try:
        with open(file_path, 'a') as results_file:
            results_file.write("####: START results of BRISE run at %s. ####\n" % experiment_current_status["start_time"].strftime("%d.%m.%Y - %H:%M:%S"))
            results_file.write("All tested configurations           : %s\n" % experiment_current_status["features"])
            results_file.write("Gave following results              : %s\n\n" % experiment_current_status["labels"])
            results_file.write("Search space size                   : %s\n" % len(experiment_current_status["search_space"]))
            results_file.write("Number of tested configurations     : %s\n" % len(experiment_current_status["features"]))
            results_file.write("Default configuration               : %s\n" % experiment_current_status["default_configuration"].get_parameters())
            results_file.write("Default configuration results       : %s\n" % experiment_current_status["default_configuration"].get_average_result())
            results_file.write("Time used for balancing             : %s\n" % str(datetime.datetime.now() - experiment_current_status["start_time"]))
            results_file.write("BRISE optimal configuration         : %s\n" % experiment_current_status["current_best_configuration"].get_parameters())
            results_file.write("BRISE optimal configuration results : %s\n" % experiment_current_status["current_best_configuration"].get_average_result())
            results_file.write("####: END results of BRISE run.                 ####\n\n\n\n")
    except IOError as error:
        logger.error("ERROR: %s occurred when tried to write final report to file." % error, exc_info=True)
