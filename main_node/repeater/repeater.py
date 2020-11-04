import logging
from abc import ABC, abstractmethod

from core_entities.configuration import Configuration
from core_entities.experiment import Experiment


class Repeater(ABC):
    def __init__(self, experiment: Experiment):

        self.logger = logging.getLogger(__name__)
        self.experiment = experiment

    @abstractmethod
    def evaluate(self, current_configuration: Configuration, experiment: Experiment):
        """
        Main logic of Repeater should be overridden in this method.
        Later, this method will be called in `evaluation_by_type` method.

        This method should return the number of repetitions to be performed for `current_configuration`
        :return: None
        """
