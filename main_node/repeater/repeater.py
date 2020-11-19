import os
from abc import ABC, abstractmethod

from core_entities.configuration import Configuration
from tools.mongo_dao import MongoDB


class Repeater(ABC):
    def __init__(self, experiment_description, experiment_id):

        self.repeater_configuration = experiment_description["Repeater"]
        self.experiment_id = experiment_id
        self.database = MongoDB(os.getenv("BRISE_DATABASE_HOST"),
                                os.getenv("BRISE_DATABASE_PORT"),
                                os.getenv("BRISE_DATABASE_NAME"),
                                os.getenv("BRISE_DATABASE_USER"),
                                os.getenv("BRISE_DATABASE_PASS"))

    @abstractmethod
    def evaluate(self, current_configuration: Configuration):
        """
        Main logic of Repeater should be overridden in this method.
        Later, this method will be called in `evaluation_by_type` method.

        This method should return the number of repetitions to be performed for `current_configuration`
        :return: None
        """
