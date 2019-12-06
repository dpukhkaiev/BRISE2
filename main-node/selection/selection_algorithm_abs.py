__doc__ = """
    Abstract class for creation of selection algorithm with needed methods and fields for ."""
import logging
from abc import ABC, abstractmethod

from core_entities.experiment import Experiment


class SelectionAlgorithm(ABC):

    def __init__(self, experiment: Experiment):
        self.experiment = experiment
        self.numOfGeneratedPoints = 0  # Counter of retrieved points from Sobol sequence.
        self.returned_points = []  # Storing previously returned points.
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def get_next_configuration(self): pass

    def __disable_point(self, point):
        """
            This method should be used to let selector know,
            that some points of search space have been already picked by prediction model.
        :param point: list. Point from search space.
        :return: None
        """
        if point not in self.returned_points:
            self.returned_points.append(point)
            return True
        else:
            self.logger.warning("WARNING! Trying to disable point that have been already retrieved(or disabled).")
            return False

    def disable_configurations(self, configurations):
        """
            This method should be used to forbid points of the Search Space that 
            have been already picked as a Model prediction.
        :param configurations: list of configurations. Configurations from search space.
        :return: None
        """
        for p in configurations:
            self.__disable_point(p)
