import datetime
import hashlib
import pickle
import json
import os
import csv
import logging
import uuid
import numpy as np

from threading import Lock
from typing import Union, List
from copy import deepcopy
from collections.abc import Mapping

from tools.front_API import API
from core_entities.configuration import Configuration
from core_entities.search_space import Hyperparameter
from tools.mongo_dao import MongoDB


class Experiment:

    def __init__(self, description: dict, search_space: Hyperparameter):
        """
        Initialization of Experiment class
        Following fields are declared:
        self.measured_configurations - list of configuration instances
                                  shape - list, e.g. ``[config_instance_1, config_instance_2, ... ]``
        self.description - description of the current experiment, it is taken from .json file
                           shape - dict with subdicts
        """
        self.logger = logging.getLogger(__name__)
        self.api = API()

        # TODO: merge lists into a single one (https://github.com/dpukhkaiev/BRISEv2/pull/112#discussion_r371761149)
        self.evaluated_configurations: List[Configuration] = []  # repeater already evaluates these configurations
        self.measured_configurations: List[Configuration] = [] # the results for these configurations are already gotten
        self._default_configuration: Configuration = None
        self._description: Mapping = description
        # TODO: search space should be decoupled from experiment (many entities require **only** search space)
        self.search_space: Hyperparameter = search_space
        self.end_time = self.start_time = datetime.datetime.now()
        # An ID that is used to differentiate Experiments by descriptions.
        self.ed_id = hashlib.sha1(json.dumps(self.description, sort_keys=True).encode("utf-8")).hexdigest()
        # A unique ID, different for every experiment (even with the same description)
        self.unique_id = str(uuid.uuid4())
        self.name: str = f"exp_{self.description['TaskConfiguration']['TaskName']}_{self.ed_id}"
        # TODO MultiOpt: Currently we store only one solution configuration here,
        #  but it was made as a possible Hook for multidimensional optimization.
        self.current_best_configurations: List[Configuration] = []
        self.bad_configurations_number = 0
        self.model_is_valid = False

        self.measured_conf_lock = Lock()
        self.evaluated_conf_lock = Lock()

        # initialize connection to the database
        self.database = MongoDB(os.getenv("BRISE_DATABASE_HOST"), 
                                os.getenv("BRISE_DATABASE_PORT"), 
                                os.getenv("BRISE_DATABASE_NAME"),
                                os.getenv("BRISE_DATABASE_USER"),
                                os.getenv("BRISE_DATABASE_PASS"))

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
        del space['database']
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
                              configurations=[default_configuration.parameters],
                              results=[default_configuration.results])
                self.measured_configurations.append(default_configuration)
                if not self.current_best_configurations:
                    self.current_best_configurations = [default_configuration]
                self.database.write_one_record(
                    "Measured_configurations",
                    default_configuration.get_configuration_record()
                )
                self.database.write_one_record(
                    collection_name="warm_startup_info",
                    record={"Exp_unique_ID": self.unique_id, "wsi": default_configuration.warm_startup_info}
                )
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
                    f"Can not add Configuration with status {configuration_instance.status.name} to Experiment.")

    def get_any_configuration_by_parameters(self, parameters: tuple) -> Union[None, Configuration]:
        """
        Find and retrieve instance of Configuration that was previously added to Experiment by it's Parameters.
        :param parameters: tuple. Parameters of desired Configuration.
        :return: instance of Configuration class or`None` if the Configuration instance was not found.
        """
        for configuration_instance in self.measured_configurations:
            if configuration_instance.parameters == parameters:
                return configuration_instance
        for configuration_instance in self.evaluated_configurations:
            if configuration_instance.parameters == parameters:
                return configuration_instance
        return None

    def get_current_status(self, serializable: bool):
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
            "Running time":
                str(self.get_running_time()) if serializable else self.get_running_time(),
            "Best found Configuration":
                self.get_current_solution().__getstate__() if serializable else self.get_current_solution(),
            "Experiment description":
                self.description,
            "Evaluated Configurations":
                [conf.__getstate__() if serializable else conf for conf in self.measured_configurations]
        }
        return current_status

    def summarize_results_to_file(self, report_format: str, folder_path: str):
        """
            Called before the BRISE proper termination. Aggregates current state of the Experiment and writes it as a
            json or yaml file.
        :param report_format: String. Format of output file, either 'yaml' or 'json'.
        :param folder_path: String. Folder, where results should be stored.
        :return: self
        """
        os.makedirs(folder_path, exist_ok=True)
        output_file_name = folder_path + self.name
        data = ""
        if report_format.lower() == "yaml":
            from yaml import safe_dump
            output_file_name += '.yaml'
            data = safe_dump(self.get_current_status(serializable=True), width=120, indent=4)
        elif report_format.lower() == "json":
            from json import dumps
            output_file_name += '.json'
            data = dumps(self.get_current_status(serializable=True), indent=4)
        else:
            self.logger.error("Wrong serialization format provided. Supported 'yaml' and 'json'.")
        with open(output_file_name, 'w') as output_file:
            output_file.write(data)
            self.logger.info("Results of the Experiment have been writen to file: %s" % output_file_name)
        return self

    def is_configuration_evaluated(self, configuration):
        """
        Check is the Configuration in the evaluated_configurations list or not.
        Could be used to filter out outdated (not added to current Experiment) Configurations.
        :param configuration: Configuration instance.
        :return: True if Configuration instance was previously added to the Experiment as those of False
        """
        return configuration in self.evaluated_configurations

    def get_final_report_and_result(self):
        self.end_time = datetime.datetime.now()
        if self.measured_configurations:
            performed_measurements = self.database.get_last_record_by_experiment_id("Repeater_measurements", self.unique_id)["Performed_measurements"]
            self.logger.info("\n\nFinal report:")

            self.logger.info("ALL MEASURED CONFIGURATIONS:\n")
            for configuration in self.measured_configurations:
                self.logger.info(configuration)
            self.logger.info("Number of measured Configurations: %s" % len(self.measured_configurations))
            self.logger.info("Number of Tasks: %s" % performed_measurements)
            self.logger.info("Best found Configuration: %s" % self.get_current_solution())
            self.logger.info("BRISE running time: %s" % str(self.get_running_time()))

            all_features = []
            for configuration in self.measured_configurations:
                all_features.append(configuration.parameters)
            results_folder = self.description["General"]["results_storage"]
            self.dump(folder_path=results_folder)  # Store instance of Experiment
            self.write_csv(folder_path=results_folder)  # Store Experiment metrics
            self.summarize_results_to_file(report_format="yaml", folder_path=results_folder)
            self.api.send('final', 'configuration',
                          configurations=[self.get_current_solution().parameters],
                          results=[self.get_current_solution().results],
                          measured_points=[all_features],
                          performed_measurements=[performed_measurements])
            return self.current_best_configurations
        else:
            self.logger.error('No configuration was measured. Please, check your Experiment Description.')

    def get_current_solution(self) -> Union[Configuration, None]:
        if self.current_best_configurations:
            return self.current_best_configurations[0]
        else:
            return None

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
        if configuration.is_better(self.get_objectives_minimization(), self.get_objectives_priorities(), self.current_best_configurations[0]):
            # we do not need warm_startup_info anymore, since better configuration was found
            self.current_best_configurations[0].warm_startup_info = {}
            self.current_best_configurations = [configuration]
            # TODO: do not transfer the solutions through main node.
            #  current flow: worker (reports) -> WSC -> repeater -> experiment -> DB -> worker (loads to continue)
            #  needed flow: worker -> DB -> worker.
            #  for this we need to (1) keep track which is the best among available solution sets and
            #                      (2) remove unneeded solutions from DB to prevent littering of storage
            self.database.update_record(
                collection_name="warm_startup_info",
                query={"Exp_unique_ID": self.unique_id},
                new_val={"wsi": configuration.warm_startup_info}
            )
        else:
            # this configuration did not improve the previous solution, no need to keep track its solutions.
            configuration.warm_startup_info = {}

        self.database.write_one_record("Measured_configurations", configuration.get_configuration_record())
        self.send_state_to_db()
        self.api.send("new", "configuration",
                      configurations=[configuration.parameters],
                      results=[configuration.results])
        self.logger.info("Adding to Experiment: %s" % configuration)

    def _add_evaluated_configuration_to_experiment(self, configuration: Configuration) -> None:
        """
        Save configuration after passing all checks.
        :param configuration: Configuration object.
        :return: None
        """
        self.evaluated_configurations.append(configuration)

    def get_objectives(self) -> List[str]:
        return self.description["TaskConfiguration"]["Objectives"]

    def get_objectives_minimization(self) -> List[bool]:
        return self.description["TaskConfiguration"]["ObjectivesMinimization"]

    def get_objectives_priorities(self) -> List[int]:
        return self.description["TaskConfiguration"]["ObjectivesPriorities"]

    def get_models_objectives_priorities(self) -> List[int]:
        return self.description["TaskConfiguration"]["ObjectivesPrioritiesModels"]

    def dump(self, folder_path: str) -> None:
        """
            Save dump of experiment object. Later it could be uploaded through the web API.
        :param folder_path: str. Path to folder, where to store dump file.
            User, which is running main.py should be authorized to write into a specified folder.
        :return: None
        """
        if folder_path[-1] != "/" and folder_path[-1] != "\\":
            folder_path = folder_path + "/"
        os.makedirs(folder_path, exist_ok=True)
        dump_path = folder_path + self.name + ".pkl"

        with open(dump_path, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)
            self.logger.info(f"Saved experiment instance. Path: {dump_path}")
        os.environ["EXP_DUMP_NAME"] = folder_path + self.name

        self.database.update_record(
            "Experiment_description",
            {"Exp_unique_ID": self.unique_id},
            {"ExperimentObject": pickle.dumps(self, pickle.HIGHEST_PROTOCOL)}
        )

    def write_csv(self, folder_path: str) -> None:
        """save .csv file with main metrics of the experiment
        Args:
            folder_path (str, optional): Path to folder, where to store the csv report.
        """
        if self.search_space.get_size() == np.inf:
            search_space_coverage = "unknown (infinite search space)"
        else:
            search_space_coverage = str(
                round((len(self.measured_configurations) / self.search_space.get_size()) * 100)
            ) + '%'

        data = dict({
            'model': "_".join([model["Type"] for model in self.description["Predictor"]["models"]]),
            'default configuration': [' '.join(
                str(v) for v in self.default_configuration.parameters)],
            'solution configuration': [' '.join(
                str(v) for v in self.get_current_solution().parameters)],
            'default result': self.default_configuration.results,
            'solution result': self.get_current_solution().results,
            'number of measured configurations': len(self.measured_configurations),
            'search space coverage': search_space_coverage,
            'number of repetitions': len(self.get_all_repetition_tasks()),
            'execution time': (self.get_running_time()).seconds,
            'repeater': self.description['Repeater']['Type']
        })

        file_path = '{0}{1}.csv'.format(folder_path, self.name)

        keys = list(data.keys())
        values = list(data.values())

        with open(file_path, 'w') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(keys)
            writer.writerow(values)
            self.logger.info("Saved csv file. Path: %s" % file_path)

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
        result_key = self.description['TaskConfiguration']['Objectives'][0]
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

    def get_repeater_parameters(self):
        return self.description["Repeater"]

    def increment_bad_configuration_number(self):
        self.bad_configurations_number = self.bad_configurations_number + 1
        return self

    def get_bad_configuration_number(self):
        return self.bad_configurations_number

    def update_model_state(self, model_state: bool):
        self.model_is_valid = model_state

    def get_model_state(self) -> bool:
        return self.model_is_valid

    def send_state_to_db(self) -> None:
        """
        Send current experiment state information, or create one if not exist.
        :return: None
        """
        if self.database.get_last_record_by_experiment_id("Experiment_state", self.unique_id) is None:
            self.database.write_one_record("Experiment_state", self.get_experiment_state_record())
        else:
            self.database.update_record(
                "Experiment_state",
                {"Exp_unique_ID": self.unique_id},
                {
                    "Number_of_measured_configs": self.get_number_of_measured_configurations(),
                    "Number_of_bad_configs": self.get_bad_configuration_number(),
                    "Current_solution": self.get_current_solution().get_configuration_record(),
                    "is_model_valid": self.get_model_state()
                }
            )

    def get_experiment_description_record(self) -> Mapping:
        '''
        The helper method that formats an experiment description to be stored as a record in a Database
        :return: Mapping. Field names of the database collection with respective information
        '''
        record = {}
        # add this specific experiment information
        record["Exp_unique_ID"] = self.unique_id
        record["Exp_ID"] = self.ed_id
        record["DateStarted"] = str(datetime.datetime.now())
        # store experiment description fields
        record.update(self.description)
        # experiment description record will be updated at the end of the experiment
        record["ExperimentObject"] = None
        return record

    def get_experiment_state_record(self) -> Mapping:
        '''
        The helper method that formats current experiment state to be stored as a record in a Database
        :return: Mapping. Field names of the database collection with respective information
        '''
        record = {}
        record["Exp_unique_ID"] = self.unique_id
        record["Number_of_measured_configs"] = self.get_number_of_measured_configurations()
        record["Number_of_bad_configs"] = self.get_bad_configuration_number()
        current_solution = self.get_current_solution()
        if current_solution is not None:
            current_solution = current_solution.get_configuration_record()
        record["Current_solution"] = current_solution
        record["is_model_valid"] = self.get_model_state()
        return record
