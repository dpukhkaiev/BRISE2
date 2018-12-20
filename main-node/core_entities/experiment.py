import logging
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
        self.all_configurations = []
        self.description = description
        self.search_space = []

    def put(self, configuration_instance):
        """
        Takes instance of Configuration class and appends it to the list with all configuration instances.
        :param configuration_instance: Object. instance of Configuration class
        """
        if self._is_valid_configuration_instance(configuration_instance):
            if self.all_configurations == []:
                self.all_configurations.append(configuration_instance)
            else:
                is_exists = False
                for value in self.all_configurations:
                    if value.get_parameters() == configuration_instance.get_parameters():
                        is_exists = True
                if not is_exists:
                    self.all_configurations.append(configuration_instance)
                    self.logger.info("Configuration %s is added to Experiment" % configuration_instance.get_parameters())

    def get(self, configuration):
        """
        Returns the instance of Configuration class, which contains the concrete configuration, if configuration the exists

        :param configuration: list. Concrete experiment configuration
               shape - list, e.g. [2900.0, 32]
        :return: instance of Configuration class
        """
        for configuration_instance in self.all_configurations:
            if configuration_instance.get_parameters() == configuration:
                return configuration_instance
        return None

    def current_best_configuration(self):

        best_configuration = [self.all_configurations[0]]
        for configuration in self.all_configurations:
            if configuration.is_better_configuration(self.description["ModelConfiguration"]["isMinimizationExperiment"],
                                                     best_configuration[0]):
                best_configuration = [configuration]
        return best_configuration

    def _is_valid_configuration_instance(self, configuration_instance):
        if isinstance(configuration_instance, Configuration):
            return True
        else:
            self.logger.error('Current object is not a Configuration instance')
            return False

