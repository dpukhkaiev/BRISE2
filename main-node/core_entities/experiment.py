import datetime
import pickle
import random
import string
import csv
import os
import itertools

import logging
from typing import List

from tools.front_API import API
from tools.file_system_io import create_folder_if_not_exists
from core_entities.configuration import Configuration


class Experiment:

    def __init__(self, description):
        """
        Initialization of Experiment class
        Following fields are declared:

        self.all_configurations - list of configuration instances
                                  shape - list, e.g. ``[config_instance_1, config_instance_2, ... ]``
        self.description - description of the current experiment, it is taken from .json file
                           shape - dict with subdicts
        self.search_space - all parameters' combinations of current experiment
                            shape - list of lists, e.g. ``[[2900, 32], [2800, 32], [2500, 32], ... ]``
        """
        self.logger = logging.getLogger(__name__)
        self.api = API()

        self.default_configuration = []
        self.all_configurations = []
        self.description = description
        self.search_space = []
        self.start_time = datetime.datetime.now()
        self.name = 'None'
        # TODO MultiOpt: Currently we store only one solution configuration here,
        #  but it was made as a possible Hook for multidimensional optimization.
        self.current_best_configurations = []
        
        self.__generate_search_space()

    def __getstate__(self):
        space = self.__dict__.copy()
        del space['api']
        del space['logger']         
        return space

    def __setstate__(self, space):
        self.__dict__ = space 
        self.logger = logging.getLogger(__name__)
        self.api = API()

    def put_default_configuration(self, default_configuration: Configuration):
        if self._is_valid_configuration_instance(default_configuration):
            if not self.default_configuration:
                self.default_configuration = default_configuration
                self.api.send("default", "configuration",
                              configurations=[default_configuration.get_parameters()],
                              results=[default_configuration.get_average_result()])
                if default_configuration not in self.all_configurations:
                    self.all_configurations.append(default_configuration)
                    self._calculate_current_best_configurations()
            else:
                raise ValueError("The default Configuration was registered already.")

    def add_configurations(self, configurations: List[Configuration]):
        """Takes the List of Configuration objects and adds it to Experiment state.
        :param configurations: List of Configuration instances.
        """
        for configuration in configurations:
            self._put(configuration)

    def _put(self, configuration_instance: Configuration):
        """
        Takes instance of Configuration class and appends it to the list with all configuration instances.
        :param configuration_instance: Configuration class instance.
        """
        if self._is_valid_configuration_instance(configuration_instance):
            if self.all_configurations is []:
                self._add_configuration_to_experiment(configuration_instance)
            else:
                is_exists = False
                for value in self.all_configurations:
                    if value.get_parameters() == configuration_instance.get_parameters():
                        is_exists = True
                if not is_exists:
                    self._add_configuration_to_experiment(configuration_instance)
                else:
                    self.logger.warning("Attempt of adding Configuration that is already in Experiment: %s" %
                                        configuration_instance)

    def get_configuration_by_parameters(self, parameters):
        """
        Returns the instance of Configuration class, which contains the concrete configuration, if configuration the exists

        :param parameters: list. Concrete experiment configuration
               shape - list, e.g. [2900.0, 32]
        :return: instance of Configuration class
        """
        for configuration_instance in self.all_configurations:
            if configuration_instance.get_parameters() == parameters:
                return configuration_instance
        return None

    def get_final_report_and_result(self, repeater):
        #   In case, if the model predicted the final point, that has less value, than the default, but there is
        # a point, that has less value, than the predicted point - report this point instead of predicted point.
        self.logger.info("\n\nFinal report:")

        self.logger.info("ALL MEASURED CONFIGURATIONS:\n")
        for configuration in self.all_configurations:
            self.logger.info(configuration)
        self.logger.info("Number of measured configurations: %s" % len(self.all_configurations))
        self.logger.info("Number of performed measurements: %s" % repeater.performed_measurements)
        self.logger.info("Best found: %s" % self.get_current_solution())

        all_features = []
        for configuration in self.all_configurations:
            all_features.append(configuration.get_parameters())
        self.api.send('final', 'configuration',
                      configurations=[self.get_current_solution().get_parameters()],
                      results=[[round(self.get_current_solution().get_average_result()[0], 2)]],
                      measured_points=[all_features],
                      performed_measurements=[repeater.performed_measurements])
        self.dump() # pickle instance

        return self.current_best_configurations

    def get_current_status(self):
        features = []
        labels = []
        for config in self.all_configurations:
            features.append(config.get_parameters())
            labels.append(config.get_average_result())

        current_status = {
            "features": features,
            "labels": labels,
            "search_space": self.search_space,
            "start_time": self.start_time,
            "current_best_configuration": self.get_current_solution(),
            "default_configuration": self.default_configuration,
            "experiment_description": self.description
        }
        return current_status

    def get_current_solution(self):
        self._calculate_current_best_configurations()
        return self.current_best_configurations[0]

    def get_current_best_configurations(self):
        self._calculate_current_best_configurations()
        return self.current_best_configurations
        
    def _is_valid_configuration_instance(self, configuration_instance):
        if isinstance(configuration_instance, Configuration):
            return True
        else:
            self.logger.error('Current object is not a Configuration instance, but %s' % type(configuration_instance))
            return False

    def _calculate_current_best_configurations(self):

        best_configuration = [self.all_configurations[0]]
        for configuration in self.all_configurations:
            if configuration.is_better_configuration(self.is_minimization(),
                                                     best_configuration[0]):
                best_configuration = [configuration]
        self.current_best_configurations = best_configuration

    def _add_configuration_to_experiment(self, configuration: Configuration) -> None:
        """
        Save configuration after passing all checks.
        This method also sends an update to API (front-end).
        :param configuration: Configuration object.
        :return: None
        """
        self.all_configurations.append(configuration)
        self.api.send("new", "configuration",
                      configurations=[configuration.get_parameters()],
                      results=[configuration.get_average_result()])
        self.logger.info("Adding to Experiment: %s" % configuration)

    def is_minimization(self):
        return self.description["General"]["isMinimizationExperiment"]

    def get_number_of_configurations_per_iteration(self):
        if "ConfigurationsPerIteration" in self.description["General"]:
            return self.description["General"]["ConfigurationsPerIteration"]
        else:
            return 0
            
    def __generate_search_space(self):
        self.search_space = [list(configuration) for configuration in itertools.product(*self.description["DomainDescription"]["AllConfigurations"])] 

    def dump(self):
        """ save instance of experiment class
        """
        # TODO: minimum requirements for dumping instance
        # generate file name
        chars = string.ascii_lowercase + string.digits
        rand_str = ''.join(random.choice(chars) for _ in range(6))
        param = str(self.get_current_solution().get_parameters())
        model = self.description['ModelConfiguration']['ModelType']
        self.name = "exp_{0}_#p{1}_{2}.{3}".format(
            model, len(self.all_configurations), param, rand_str)
        os.environ["EXP_DUMP_NAME"] = self.name

        create_folder_if_not_exists('Results/serialized/')
        file_path = 'Results/serialized/{}.pkl'.format(self.name)
        self.end_time = datetime.datetime.now()

        # write pickl
        with open(file_path, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)
            self.logger.info("Saved experiment instance. Path: %s" % file_path)
        
        # write csv
        self.write_csv()

    def write_csv(self, path='Results/serialized/'):
        """save .csv file with main metrics of the experiment
        
        Args:
            final (bool, optional): Is the Experiment finished?. Defaults to False.
        """

        search_space = 1
        for dim in self.description['DomainDescription']['AllConfigurations']:
            search_space *= len(dim)

        data = dict({
            'model': self.description['ModelConfiguration']['ModelType'],
            'default configuration': [' '.join(
                str(v) for v in self.default_configuration.get_parameters())],
            'solution configuration': [' '.join(
                str(v) for v in self.get_current_solution().get_parameters())],
            'default result': self.default_configuration.get_average_result()[0],
            'solution result': self.get_current_solution().get_average_result()[0],
            'result improvement': str(round(self.get_solution_relative_impr(), 1)) + '%',
            'number of measured configurations': len(self.all_configurations),
            'search space coverage': str(round((len(self.all_configurations)/search_space)*100)) + '%',
            'number of repetitions': len(self.get_all_repetition_tasks()),
            'execution time': (self.end_time - self.start_time).seconds,
            'repeater': self.description['Repeater']['Type']
        })

        file_path = '{0}{1}.csv'.format(path, self.name)

        keys = list(data.keys())
        values = list(data.values())

        with open(file_path, 'a') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(keys)
            writer.writerow(values)
            self.logger.info("Saved csv file. Path: %s" % file_path)

    def get_name(self):
        return self.name

    def get_solution_relative_impr(self):
        """Deviation of a solution result relative to the default value
        
        Returns:
            [Float] -- Round number in percent
        """
        default_avg_result = self.default_configuration.get_average_result()[0]
        solution_avg_result = self.get_current_solution().get_average_result()[0]
        return (default_avg_result - solution_avg_result)/default_avg_result*100

    def get_all_repetition_tasks(self):
        """ List of results for all tasks that were received on workers
        
        Returns:
            [List] -- List with results for all atom-tasks
        """

        all_tasks = []
        result_key = self.description['TaskConfiguration']['ResultStructure'][0]
        for configuration in self.all_configurations:
            for task in configuration.get_tasks().values():
                if 'result' in task:
                    all_tasks.append(task['result'][result_key])
        return all_tasks

    def get_number_of_measured_configurations(self):
        return len(self.all_configurations)

    def get_search_space_size(self):
        return len(self.search_space)

    def get_stop_condition_parameters(self):
        return self.description["StopCondition"]
    
    def get_selection_algorithm_parameters(self):
        return self.description["SelectionAlgorithm"]