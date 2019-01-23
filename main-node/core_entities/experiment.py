import logging
from core_entities.configuration import Configuration
from tools.front_API import API


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
        # Send updates to subscribers
        self.sub = API()

        self.default_configuration = []
        self.all_configurations = []
        self.description = description
        self.search_space = []
        self.current_best_configuration = []
        self.start_time = None

    def put_start_time(self, start_time):
        self.start_time = start_time

    def put_default_configuration(self, default_configuration):
        self.default_configuration = default_configuration

    def put(self, configuration_instance):
        """
        Takes instance of Configuration class and appends it to the list with all configuration instances.
        :param configuration_instance: Object. instance of Configuration class
        """
        if self._is_valid_configuration_instance(configuration_instance):
            if self.all_configurations == []:
                self.all_configurations.append(configuration_instance)
                self.current_best_configuration = [configuration_instance]
            else:
                is_exists = False
                for value in self.all_configurations:
                    if value.get_parameters() == configuration_instance.get_parameters():
                        is_exists = True
                if not is_exists:
                    self.all_configurations.append(configuration_instance)
                    self.logger.info("Configuration %s is added to Experiment" % configuration_instance.get_parameters())
                    self.current_best_configuration = self._calculate_current_best_configuration()
                    if self.current_best_configuration[0] == configuration_instance:
                        self.logger.info("New solution found: %s with result %s" % (configuration_instance.get_parameters(),
                                                                        configuration_instance.get_average_result()))

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

    def get_final_report_and_result(self, repeater):
        #   In case, if the model predicted the final point, that has less value, than the default, but there is
        # a point, that has less value, than the predicted point - report this point instead of predicted point.

        self.logger.info("\n\nFinal report:")

        temp_message = ("Configuration: %s Quality: %s, "
                        "Solution that model gave is worse that one of measured previously, but better than default."
                        "Reporting best of measured." % (self.current_best_configuration[0].get_parameters(),
                                                         self.current_best_configuration[0].get_average_result()))
        self.logger.info(temp_message)
        self.sub.send('log', 'info', message=temp_message)

        self.logger.info("ALL MEASURED CONFIGURATIONS:\n")
        for configuration in self.all_configurations:
            self.logger.info("%s: %s" % (str(configuration.get_parameters()), str(configuration.get_average_result())))
        self.logger.info("Number of measured points: %s" % len(self.all_configurations))
        self.logger.info("Number of performed measurements: %s" % repeater.performed_measurements)
        self.logger.info("Best found point: %s, with configuration: %s"
                         % (self.current_best_configuration[0].get_average_result(),
                            self.current_best_configuration[0].get_parameters()))

        all_features = []
        for configuration in self.all_configurations:
            all_features.append(configuration.get_parameters())
        self.sub.send('final', 'configuration',
                      configurations=[self.current_best_configuration[0].get_parameters()],
                      results=[[round(self.current_best_configuration[0].get_average_result()[0], 2)]],
                      measured_points=[all_features],
                      performed_measurements=[repeater.performed_measurements])

        return self.current_best_configuration

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
            "current_best_configuration": self.current_best_configuration,
            "default_configuration": self.default_configuration,
            "experiment_description": self.description
        }
        return current_status

    def _is_valid_configuration_instance(self, configuration_instance):
        if isinstance(configuration_instance, Configuration):
            return True
        else:
            self.logger.error('Current object is not a Configuration instance')
            return False

    def _calculate_current_best_configuration(self):

        best_configuration = [self.all_configurations[0]]
        for configuration in self.all_configurations:
            if configuration.is_better_configuration(self.description["ModelConfiguration"]["isMinimizationExperiment"],
                                                     best_configuration[0]):
                best_configuration = [configuration]
        return best_configuration
