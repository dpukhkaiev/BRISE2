import logging


class Experiment:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.all_configurations = []  # list with instances of Configuration class
        self.description = {}  # task config
        self.search_space = []  # full search space of the experiment, shape - list of lists

    def put(self, configuration_instance):
        """
        Takes instance of Configuration class and appends it to the list with all configuration instances.
        :param configuration_instance: Object. instance of Configuration class
        """
        if self.all_configurations == []:
            self.all_configurations.append(configuration_instance)
        else:
            is_exists = False
            for value in self.all_configurations:
                if value.configuration == configuration_instance.configuration:
                    is_exists = True
            if not is_exists:
                self.all_configurations.append(configuration_instance)
                self.logger.info("Configuration %s has added to Experiment" % value.configuration)

    def get(self, configuration):
        """
        Returns the instance of Configuration class, which contains the concrete configuration, if configuration the exists

        :param configuration: list. Concrete experiment configuration
               shape - list, e.g. [2900.0, 32]
        :return: instance of Configuration class
        """
        for configuration_instance in self.all_configurations:
            if configuration_instance.configuration == configuration:
                return configuration_instance
        return None
