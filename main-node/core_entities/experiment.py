import logging
import datetime
from typing import List


from tools.front_API import API
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

        # TODO MultiOpt: Currently we store only one solution configuration here,
        #  but it was made as a possible Hook for multidimensional optimization.
        self.current_best_configurations = []

    def put_default_configuration(self, default_configuration: Configuration):
        if self._is_valid_configuration_instance(default_configuration):
            if not self.default_configuration:
                self.default_configuration = default_configuration
                self.api.send("default", "configuration",
                              configurations=[default_configuration.get_parameters()],
                              results=[default_configuration.get_average_result()])
                if default_configuration not in self.all_configurations:
                    self.all_configurations.append(default_configuration)
                    self.current_best_configurations = self._calculate_current_best_configurations()
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
        self.logger.info("Number of measured points: %s" % len(self.all_configurations))
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
        self.current_best_configurations = self._calculate_current_best_configurations()
        return self.current_best_configurations[0]

    def _is_valid_configuration_instance(self, configuration_instance):
        if isinstance(configuration_instance, Configuration):
            return True
        else:
            self.logger.error('Current object is not a Configuration instance, but %s' % type(configuration_instance))
            return False

    def _calculate_current_best_configurations(self):

        best_configuration = [self.all_configurations[0]]
        for configuration in self.all_configurations:
            if configuration.is_better_configuration(self.description["ModelConfiguration"]["isMinimizationExperiment"],
                                                     best_configuration[0]):
                best_configuration = [configuration]
        return best_configuration

    def _add_configuration_to_experiment(self, configuration: Configuration) -> None:
        """
        Save configuration after passing all checks.
        This method also sends an update to API (front-end), calculates current best Configuration.
        :param configuration: Configuration object.
        :return: None
        """
        self.all_configurations.append(configuration)
        self.api.send("new", "configuration",
                      configurations=[configuration.get_parameters()],
                      results=[configuration.get_average_result()])
        self.logger.info("Adding to Experiment: %s" % configuration)
        self.current_best_configurations = self._calculate_current_best_configurations()
        if self.get_current_solution() == configuration:
            self.logger.info("New solution found: %s" % configuration)


