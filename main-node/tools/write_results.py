__doc__ = """
Writing results of BRISE run to the output file."""

import datetime
import itertools
import logging

from tools.file_system_io import create_folder_if_not_exists


def write_results(global_config, experiment_description, time_started, configurations,
                  performed_measurements, optimal_configuration, default_configurations):

    logger = logging.getLogger(__name__)
    create_folder_if_not_exists(global_config["results_storage"])
    search_space = list(itertools.product(*experiment_description["DomainDescription"]["AllConfigurations"]))

    # TODO: LOGFILE parameter should be chosen according to the name of file, that provides Experiment description
    file_path = "%sBRISE_Results_for_%s.txt" % (global_config["results_storage"],
                                                experiment_description["TaskConfiguration"]["WorkerConfiguration"]["ws_file"])
    features = []
    labels = []
    for config in configurations:
        features.append(config.configuration)
        labels.append(config.average_result)
    try:
        with open(file_path, 'a') as results_file:
            results_file.write("####: START results of BRISE run at %s. ####\n" % time_started.strftime("%d.%m.%Y - %H:%M:%S"))
            results_file.write("All tested configurations           : %s\n" % features)
            results_file.write("Gave following results              : %s\n\n" % labels)
            results_file.write("Search space size                   : %s\n" % len(search_space))
            results_file.write("Number of tested configurations     : %s\n" % len(features))
            results_file.write("Number of performed experiments     : %s\n" % performed_measurements)
            results_file.write("Default configuration               : %s\n" % default_configurations[0].configuration)
            results_file.write("Default configuration results       : %s\n" % default_configurations[0].average_result)
            results_file.write("Time used for balancing             : %s\n" % str(datetime.datetime.now() - time_started))
            results_file.write("BRISE optimal configuration         : %s\n" % optimal_configuration[0].configuration)
            results_file.write("BRISE optimal configuration results : %s\n" % optimal_configuration[0].average_result)
            results_file.write("####: END results of BRISE run.                 ####\n\n\n\n")
    except IOError as e:
        logger.error("ERROR: %s occurred when tried to write final report to file." % e, exc_info=True)
