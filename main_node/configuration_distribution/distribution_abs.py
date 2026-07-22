from abc import ABC, abstractmethod
import logging

class AbstractDistribution(ABC):

    def __init__(self, config: dict):

        self.logger = logging.getLogger(self.__class__.__name__)
        pass

    @abstractmethod
    def handle_configuration_distribution(self, experiment_id, body):
        pass

    @abstractmethod
    def dispatch(self, experiment_id, body):
        pass

    @abstractmethod
    def first_it(self, experiment_id):
        pass