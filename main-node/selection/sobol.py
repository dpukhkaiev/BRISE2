__doc__ = """
    Describes logic of selection algorithm based on Sobol sequences in Sobol space."""

import sobol_seq
import math

from selection.selection_algorithm_abs import SelectionAlgorithm
from core_entities.search_space import HyperparameterType


class SobolSequence(SelectionAlgorithm):
    def __init__(self, experiment):
        """
        Creates SobolSequence instance that stores information about number of generated points
        :param experiment: the instance of Experiment class
        """
        super().__init__(experiment)
        self.dimensionality = len(self.experiment.search_space.get_hyperparameter_names())

    def __generate_sobol_vector(self):
        """
            Generates a next sobol vector in the current search space.
            :return: sobol vector as numpy array.
        """

        # https://github.com/naught101/sobol_seq#usage
        vector, _ = sobol_seq.i4_sobol(self.dimensionality, self.numOfGeneratedPoints + 1)
        self.numOfGeneratedPoints += 1

        return vector

    def get_next_configuration(self):
        """
            Will return next data point from initiated Sobol sequence imposed to the search space.
        :return: list - point in current search space.
        """
        # TODO: It is possible to encapsulate control of 'getting stuck while retrieving unique point from selector'
        # Getting next point from sobol sequence.
        point = self.__generate_sobol_vector()

        values = {}
        # TODO: Access of search space object should be direct (need to solve it during Feature transformation)
        search_space = self.experiment.search_space
        for index, hyperparameter_name in enumerate(search_space.get_hyperparameter_names()):
            # TODO: Feature transformation should be encapsulated. This code will be refactored.
            value = None
            hyperparameter_type = search_space.get_hyperparameter_type(hyperparameter_name)
            if hyperparameter_type is HyperparameterType.NUMERICAL_INTEGER:
                lower, upper = search_space.get_hyperparameter_boundaries(hyperparameter_name)
                value = lower + math.floor(point[index] * (upper - lower))
            elif hyperparameter_type is HyperparameterType.NUMERICAL_FLOAT:
                lower, upper = search_space.get_hyperparameter_boundaries(hyperparameter_name)
                value = lower + point[index] * (upper - lower)
            elif hyperparameter_type in (HyperparameterType.CATEGORICAL_ORDINAL, HyperparameterType.CATEGORICAL_NOMINAL):
                #  Sobol cannot differentiate between ordinal and nominal types.
                choices = search_space.get_hyperparameter_categories(hyperparameter_name)
                choice_number = math.floor(point[index] * len(choices))
                value = choices[choice_number]
            else:
                raise TypeError(f"Hyperparameter {hyperparameter_type} is not supported by Sobol selection algorithm!")
            values[hyperparameter_name] = value

        # check conditions for conditional parameters and disable some parameters if needed
        for hyperparameter_name in search_space.get_hyperparameter_names():
            conditions = search_space.get_conditions_for_hyperparameter(hyperparameter_name)
            for condition in conditions:
                if values[condition] not in conditions[condition]:
                    values[hyperparameter_name] = None

        candidate = self.experiment.search_space.create_configuration(values=values)

        try:
            self.logger.debug("Retrieving new configuration from the Sobol sequence: %s" % str(candidate))
            return candidate
        except Exception:
            self.logger.error("Selector was not able to get new configuration!")
