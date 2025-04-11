__doc__ = """
Mock for main module for running BRISE configuration balancing."""

import pickle
import time
import logging
import os

from core_entities.experiment import Experiment
from WorkerServiceClient.WSClient_sockets import WSClient
from tools.front_API import API
from logger.default_logger import BRISELogConfigurator
from repeater.repeater import Repeater


if __name__ == "__main__":
    logger = BRISELogConfigurator().get_logger(__name__)
else:
    logger = logging.getLogger(__name__)


class LoggerStub(logging.Logger):
    pass


class ApiStub(API):
    pass


def run(experiment_description=None, mock_data_file=None):
    try:
        with open(mock_data_file, 'rb') as f:
            mock_data = pickle.loads(f.read())
    except IOError or pickle.UnpicklingError as e:
        logger.error("Unable to load saved MOCK data: %s" % e, exc_info=True)
        exit(1)

    # ------------------------------------------------------
    # Scenario:
    # 1. Sending experiment description.
    # 2. Measuring and sending default configuration.
    # 3. Measuring initial configurations.          (Currently - 4 pc).
    # 4. Building model and sending predictions:
    #   If model adequate:                          (6 last models)
    #       5. Predicting configuration, measuring, sending to the front-end.
    #   else: (model not adequate)                  (6 first models)
    #       5. Getting new configuration from Sobol.
    # 6. Evaluating Stop Condition:
    #   If terminating:
    #       7. Reporting the solution (in summary - 17 Configurations was evaluated (including default and Solution).
    #   else:
    #       7. Go to 4.
    # ------------------------------------------------------
    # Saved data is a dictionary with following keyed parameters:
    # 'Models and configurations': Chronological List of models and corresponding configurations used to build a model.
    # 'Solution configuration':
    # 'Initial configurations':
    # 'Default configuration':
    # 'Global config': Dict for initial config.
    # 'Experiment': Experiment object dumped after initialization.

    #  --- Presets
    sleep_between_messages = 2  # In seconds. One second + ~25 seconds to overall running for current version of mock.
    api = API()
    os.makedirs('./Results/', exist_ok=True)
    # --- Fixing dump issues (APIs and Logging objects were cut off).
    # Removing all tasks from configurations to fix repetitions.
    for state in mock_data["Models and configurations"]:
        state["Model"].logger = logging.getLogger("configuration_selection/model")
        state["Model"].sub = API()
        for config in state["Configurations"]:
            config.logger = logging.getLogger("core_entities.configuration.py")

    # --- Start actual imitation.
    experiment = Experiment(mock_data["Experiment"].description, mock_data["Experiment"].search_space)
    api.send('experiment', 'description', global_config=mock_data["Global config"],
             experiment_description=experiment.description,
             searchspace_description=experiment.search_space.generate_searchspace_description())

    # for config in [experiment.default_configuration, *mock_data["Solution configuration"], *mock_data["Initial configurations"]]:
    #     config.logger = logging.getLogger("core_entities.configuration.py")
    mock_data["Models and configurations"].pop()

    worker_service_client = WSClient(experiment.description["TaskConfiguration"], 'w_service:49153', "MOCK_WSC.log")

    # Creating runner for experiments that will repeat the configuration measurement to avoid fluctuations.
    repeater = Repeater(worker_service_client, experiment)
    logger.info("Measuring default configuration that we will used in regression to evaluate solution")

    # Sending default configuration.
    experiment.search_space.set_default_configuration(mock_data["Default configuration"])
    for task in mock_data["Default configuration"].get_tasks().keys():
        api.send('new', 'task', configurations=[mock_data["Default configuration"].get_parameters()], results=[mock_data["Default configuration"].get_tasks()[task]])
        time.sleep(sleep_between_messages)
    repeater.performed_measurements += len(mock_data["Default configuration"].get_tasks())
    experiment.put_default_configuration(mock_data["Default configuration"])

    logger.info("Measuring initial Configurations")  # Initial configuration included into the first model.
    for state_num, state in enumerate(mock_data['Models and configurations']):
        # Select new configurations.
        new_configs = []
        for config in state['Configurations']:
            config_is_new = True
            for prev_config in experiment.measured_configurations:
                if config.get_parameters() == prev_config.get_parameters():
                    config_is_new = False
            if config_is_new:
                new_configs.append(config)
        # Measure new configurations (selecting needed number of tasks from each of configurations)
        for config in new_configs:
            repeater.performed_measurements += len(config.get_tasks())
            for task in config.get_tasks().keys():
                api.send('new', 'task', configurations=[config.get_parameters()], results=[config.get_tasks()[task]])
                time.sleep(sleep_between_messages)
            experiment.add_configurations([config])

        number_of_configurations_in_iteration = experiment.get_number_of_configurations_per_iteration()
        # Imitation of building the model, regression prediction:
        state["Model"].predict_next_configurations(number_of_configurations_in_iteration)
        api.send("log", "info", message="Built models is%s valid!" % ("" if state["Adequate"] else " NOT"))

    # At this point stop condition said "Stop"
    experiment.get_final_report_and_result(repeater)


class A:
    @staticmethod
    def emit(*args):
        print("API MESSAGE: ", end='')
        print(args)


if __name__ == "__main__":
    """
    For the unit tests running - put following statements above WSClient importing:
from os import chdir
from os.path import abspath
from sys import path
chdir('..')
path.append(abspath('.'))
    """
    API(A())
    start = time.time()
    run()
    logger.info("Mock running time: %s(sec)." % round(time.time() - start))
