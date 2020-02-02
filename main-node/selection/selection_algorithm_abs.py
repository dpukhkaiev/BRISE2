__doc__ = """
    Abstract class for creation of selection algorithm with needed methods and fields for ."""
import logging
from abc import ABC, abstractmethod

from core_entities.experiment import Experiment
from core_entities.configuration import Configuration


class SelectionAlgorithm(ABC):

    def __init__(self, experiment: Experiment):
        self.experiment = experiment
        self.numOfGeneratedPoints = 0  # Counter of retrieved points from selector
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def get_next_configuration(self): pass
