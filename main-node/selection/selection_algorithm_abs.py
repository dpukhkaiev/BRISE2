__doc__ = """
    Abstract class for creation of selection algorithm with needed methods and fields for ."""
import logging
from abc import ABC, abstractmethod

from core_entities.experiment import Experiment
from core_entities.configuration import Configuration


class SelectionAlgorithm(ABC):

    def __init__(self, experiment: Experiment):
        self.experiment = experiment
        self.numOfGeneratedPoints = 0  # Counter of retrieved points from Sobol sequence.
        self.returned_points = []  # Storing previously returned points.
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def get_next_configuration(self): pass

    def disable_configuration(self, configuration: Configuration):
        """
            This method should be used to let selector know,
            that some configurations have been already picked by prediction model.
        :param configuration: Configuration. Configuration from search space.
        :return: None
        """
        if configuration not in self.returned_points:
            self.returned_points.append(configuration)
            return True
        else:
            self.logger.warning("WARNING! Trying to disable configuration that have been already retrieved (or disabled).")
            return False

    def _is_unique_config(self, configuration: Configuration):
        if configuration not in self.returned_points and configuration is not None:
            if self.disable_configuration(configuration):            
                return True
            else:
                return False
        else:
            return False

