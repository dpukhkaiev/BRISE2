from configuration_distribution.distribution_abs import AbstractDistribution
from tools.reflective_class_import import reflective_class_import
import logging


class ConfigurationDistributionOrchestrator:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_distribution(self, distribution_description: dict) -> AbstractDistribution:
        """
        Returns an instance of a distribution algorithm based on the provided configuration.

        :param distribution_description: experiment config (dict) with one key, 
                                         whose value is a dict including a "Type" field.
        :return: an instantiated AbstractDistribution subclass.
        """

        dist_name = [key for key in distribution_description
                    if isinstance(distribution_description[key], dict)
                    and "Type" in distribution_description[key]][0]

        distribution_type = distribution_description[dist_name]["Type"]

        distribution_class = reflective_class_import(
            class_name=distribution_type,
            folder_path="configuration_distribution"
        )
        
        return distribution_class(distribution_description)
    