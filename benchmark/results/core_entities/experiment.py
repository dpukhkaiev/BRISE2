import datetime
import hashlib
import pickle
import json
import os
import logging
from threading import Lock
from typing import Union, List
from copy import deepcopy

from tools.front_API import API
from tools.file_system_io import create_folder_if_not_exists
from core_entities.configuration import Configuration


class Experiment:

    def __init__(self, description: dict):
        """
        Initialization of Experiment class
        Following fields are declared:
        self.measured_configurations - list of configuration instances
                                  shape - list, e.g. ``[config_instance_1, config_instance_2, ... ]``
        """
        self.logger = logging.getLogger(__name__)
        self.api = API()

        # TODO: merge lists into a single one (https://github.com/dpukhkaiev/BRISEv2/pull/112#discussion_r371761149)
        self.evaluated_configurations: List[Configuration] = []  # repeater already evaluates these configurations
        self.measured_configurations: List[Configuration] = [] # the results for these configurations are already gotten
        self._default_configuration: Configuration = None
        self._description: dict = description
        self.end_time = self.start_time = datetime.datetime.now()
        # A unique ID that is used to differentiate Experiments by descriptions.
        self.id = hashlib.sha1(json.dumps(self.description, sort_keys=True).encode("utf-8")).hexdigest()
        self.name: str = f"exp_{self.description['TaskConfiguration']['TaskName']}_{self.id}"
        # TODO MultiOpt: Currently we store only one solution configuration here,
        #  but it was made as a possible Hook for multidimensional optimization.
        self.current_best_configurations: List[Configuration] = []
        self.bad_configurations_number = 0
        self.model_is_valid = False

        self.measured_conf_lock = Lock()
        self.evaluated_conf_lock = Lock()

    def _get_description(self):
        return deepcopy(self._description)

    def _set_description(self, description):
        if not self._description:
            self._description = description
        else:
            self.logger.error("Unable to update Experiment Description: Read-only property.")
            raise AttributeError("Unable to update Experiment Description: Read-only property.")

    def _del_description(self):
        if self._description:
            self.logger.error("Unable to delete Experiment Description: Read-only property.")
            raise AttributeError("Unable to update Experiment Description: Read-only property.")

    description = property(_get_description, _set_description, _del_description)

    def __getstate__(self):
        space = self.__dict__.copy()
        del space['api']
        del space['logger']
        del space['measured_conf_lock']
        del space['evaluated_conf_lock']
        return space

    def __setstate__(self, space):
        self.__dict__ = space
        self.logger = logging.getLogger(__name__)
        self.api = API()

        # for thread-safe adding value to relevant array; protection against duplicates configurations
        self.measured_conf_lock = Lock()
        self.evaluated_conf_lock = Lock()

    @property
    def default_configuration(self) -> Configuration:
        return self._default_configuration

    @default_configuration.setter
    def default_configuration(self, default_configuration: Configuration):
        if self._is_valid_configuration_instance(default_configuration):
            if not self._default_configuration:
                self._default_configuration = default_configuration
                self.api.send("default", "configuration",
                              configurations=[default_configuration.hyperparameters],
                              results=[default_configuration.results])
                self.measured_configurations.append(default_configuration)
                if not self.current_best_configurations:
                    self.current_best_configurations = [default_configuration]
                temp_msg = f"Added Default Configuration: {default_configuration}"
                self.logger.info(temp_msg)
                self.api.send('log', 'info', message=temp_msg)
            else:
                raise ValueError("The default Configuration was registered already.")

    def try_add_configuration(self, configuration: Configuration):
        """
        Add a Configuration object to the Experiment, if the Configuration was now added previously.
        :param configuration: Configuration instance.
        :return bool flag, True if the Configuration was added to list of either measured or evaluated configurations,
        False if not.
        """
        result = False
        if configuration.is_enabled:
            if self._try_put(configuration):
                # configuration will not be added to the Experiment if it is already there
                result = True
        return result

    def _try_put(self, configuration_instance: Configuration):
        """
        Takes instance of Configuration class and appends it to the list with all configuration instances.
        :param configuration_instance: Configuration class instance.
        :return bool flag, is _put add configuration to any lists or not
        """
        if self._is_valid_configuration_instance(configuration_instance):
            if configuration_instance.status == Configuration.Status.MEASURED:
                with self.measured_conf_lock:
                    if configuration_instance not in self.measured_configurations:
                        self._add_measured_configuration_to_experiment(configuration_instance)
                        return True
                    else:
                        return False
            elif configuration_instance.status == Configuration.Status.EVALUATED:
                with self.evaluated_conf_lock:
                    if configuration_instance not in self.evaluated_configurations:
                        self._add_evaluated_configuration_to_experiment(configuration_instance)
                        return True
                    else:
                        return False
            else:
                raise ValueError(
                    f"Can not add Configuration with status {configuration_instance.status} to Experiment.")

    def get_any_configuration_by_parameters(self, hyperparameters: tuple) -> Union[None, Configuration]:
        """
        Find and retrieve instance of Configuration that was previously added to Experiment by it's hyperparameters.
        :param hyperparameters: tuple. hyperparameters of desired Configuration.
        :return: instance of Configuration class or`None` if the Configuration instance was not found.
        """
        for configuration_instance in self.measured_configurations:
            if configuration_instance.hyperparameters == hyperparameters:
                return configuration_instance
        for configuration_instance in self.evaluated_configurations:
            if configuration_instance.hyperparameters == hyperparameters:
                return configuration_instance
        return None

    def is_configuration_in_experiment(self, configuration: Configuration) -> bool:
        """
        Check if provided Configuration already in Experiment.

        :param configuration: BRISE Configuration instance with required 'hyperparameters' property.
        :type configuration: Configuration
        :return: boolean True if Configuration was previously added to Experiment, False otherwise.
        :rtype bool
        """
        found_config = self.get_any_configuration_by_parameters(configuration.hyperparameters)
        return True if found_config else False

    def is_configuration_evaluated(self, configuration):
        """
        Check is the Configuration in the evaluated_configurations list or not.
        Could be used to filter out outdated (not added to current Experiment) Configurations.
        :param configuration: Configuration instance.
        :return: True if Configuration instance was previously added to the Experiment as those of False
        """
        return configuration in self.evaluated_configurations

    def get_final_report_and_result(self, repeater):
        self.end_time = datetime.datetime.now()
        if self.measured_configurations:
            self.logger.info("\n\nFinal report:")

            self.logger.info("ALL MEASURED CONFIGURATIONS:\n")
            for configuration in self.measured_configurations:
                self.logger.info(configuration)
            self.logger.info("Number of measured Configurations: %s" % len(self.measured_configurations))
            self.logger.info("Number of Tasks: %s" % repeater.performed_measurements)
            self.logger.info("Best found Configuration: %s" % self.get_current_solution())
            self.logger.info("BRISE running time: %s" % str(self.get_running_time()))

            all_features = []
            for configuration in self.measured_configurations:
                all_features.append(configuration.hyperparameters)
            self.dump()  # Store instance of Experiment
            self.api.send('final', 'configuration',
                        configurations=[self.get_current_solution().hyperparameters],
                        results=[self.get_current_solution().results],
                      measured_points=[all_features],
                      performed_measurements=[repeater.performed_measurements])
            return self.current_best_configurations
        else:
            self.logger.error('No configuration was measured. Please, check your Experiment Description.')

    def get_current_status(self, serializable: bool = False):
        """
            Returns current state of Experiment, including already elapsed time, currently found solution Configuration,
        default Configuration, Experiment description and all already evaluated Configurations.

        :param serializable: Boolean.
            Defines if returned structure should be serializable or not. If True - all Configuration objects will be
        transformed to their string representation.
        :return: Dict with following keys["Running time", "Best found Configuration",
                                        "Default configuration", "Experiment description",
                                        "Evaluated Configurations"]
        """
        current_status = {
            "Running time": str(self.get_running_time()) if serializable else self.get_running_time(),
            "Best found Configuration": self.get_current_solution().__getstate__() if serializable else self.get_current_solution(),
            "Default configuration": self.default_configuration.__getstate__() if serializable else self.default_configuration,
            "Experiment description": self.description,
            "Evaluated Configurations": [conf.__getstate__() if serializable else conf for conf in self.measured_configurations]
        }
        return current_status

    def get_current_solution(self) -> Configuration:
        return self.current_best_configurations[0]

    def _is_valid_configuration_instance(self, configuration_instance: Configuration) -> bool:
        if isinstance(configuration_instance, Configuration):
            return True
        else:
            self.logger.error('Current object is not a Configuration instance, but %s' % type(configuration_instance))
            return False

    def _add_measured_configuration_to_experiment(self, configuration: Configuration) -> None:
        """
        Save configuration after passing all checks.
        This method also sends an update to API (front-end).
        :param configuration: Configuration object.
        :return: None
        """
        self.measured_configurations.append(configuration)
        if not self.current_best_configurations:
            # first soultion found
            self.current_best_configurations = [configuration]
        elif configuration.is_better_configuration(self.is_minimization(), self.current_best_configurations[0]):
            # new solution found
            self.current_best_configurations[0].warm_startup_info = {}
            self.current_best_configurations = [configuration]
        else:
            # this configuration did not improve the previous solution
            configuration.warm_startup_info = {}

        self.api.send("new", "configuration",
                      configurations=[configuration.hyperparameters],
                      results=[configuration.results])
        self.logger.info("Adding to Experiment: %s" % configuration)

    def _add_evaluated_configuration_to_experiment(self, configuration: Configuration) -> None:
        """
        Save configuration after passing all checks.
        :param configuration: Configuration object.
        :return: None
        """
        self.evaluated_configurations.append(configuration)

    def is_minimization(self):
        return self.description["General"]["isMinimizationExperiment"]

    def dump(self, folder_path: str = 'Results/serialized/'):
        """ save instance of experiment class
        """
        # Used to upload Experiment dump through web API
        os.environ["EXP_DUMP_NAME"] = self.name

        create_folder_if_not_exists(folder_path)
        file_name = '{}.pkl'.format(self.name)
        # write pickle
        with open(folder_path + file_name, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)
            self.logger.info("Saved experiment instance. Path: %s" % (folder_path + file_name))

    def get_name(self):
        return self.name

    def get_running_time(self):
        if self.end_time is self.start_time:
            return datetime.datetime.now() - self.start_time
        else:
            return self.end_time - self.start_time

    def get_all_repetition_tasks(self):
        """ List of results for all tasks that were received on workers
        
        Returns:
            [List] -- List with results for all atom-tasks
        """

        all_tasks = []
        result_key = self.description['TaskConfiguration']['ResultStructure'][0]
        for configuration in self.measured_configurations:
            for task in configuration.get_tasks().values():
                if 'result' in task:
                    all_tasks.append(task['result'][result_key])
        return all_tasks

    def get_number_of_measured_configurations(self):
        return len(self.measured_configurations)

    def get_stop_condition_parameters(self):
        return self.description["StopCondition"]

    def get_selection_algorithm_parameters(self):
        return self.description["SelectionAlgorithm"]

    def get_outlier_detectors_parameters(self):
        return self.description["OutliersDetection"]

    def increment_bad_configuration_number(self):
        self.bad_configurations_number = self.bad_configurations_number + 1
        return self

    def get_bad_configuration_number(self):
        return self.bad_configurations_number

    def update_model_state(self, model_state: bool):
        self.model_is_valid = model_state

    def get_model_state(self) -> bool:
        return self.model_is_valid
