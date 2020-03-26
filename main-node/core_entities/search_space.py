import logging
import numpy as np

from typing import Union, Dict, List
from copy import deepcopy
from enum import Enum

from ConfigSpace.configuration_space import Configuration as CSConfiguration
from ConfigSpace import InCondition, EqualsCondition
from ConfigSpace.read_and_write import json as CSjson
from ConfigSpace.exceptions import ForbiddenValueError
from ConfigSpace.hyperparameters import Hyperparameter
from ConfigSpace import UniformIntegerHyperparameter, UniformFloatHyperparameter, OrdinalHyperparameter, CategoricalHyperparameter

from core_entities.configuration import Configuration


class HyperparameterType(Enum):
    """
    Defined types of Hyperparameters supported in BRISE.

    The following binding from ConfigSpace JSON Hyperparameter description to BRISE was done:
    uniform_int     ->  NUMERICAL_INTEGER - Integer values between 'lower' and 'upper' bounds, finite number of variants.
    uniform_float   ->  NUMERICAL_FLOAT   - Float values between 'lower' and 'upper' bounds, infinite number of variants.
    ordinal         ->  CATEGORICAL_ORDINAL - Defined set of "choices", where notions of order and median applicable.
    categorical     ->  CATEGORICAL_NOMINAL - Defined set of "choices". Notions of order and median are NOT applicable.
    """
    NUMERICAL_INTEGER = 1
    NUMERICAL_FLOAT = 2
    CATEGORICAL_NOMINAL = 3
    CATEGORICAL_ORDINAL = 4


class SearchSpace:

    def __init__(self, domain_description: dict):
        self.logger = logging.getLogger(__name__)

        # load ConfigurationSpace object from Domain Description file.
        with open(domain_description["DataFile"], 'r') as f:
            self._config_space = CSjson.read(f.read())

        # initialize search space from ConfigurationSpace object
        self.search_space_size = None
        self.__hyperparameter_names = domain_description["HyperparameterNames"]

        # initialize default configuration, if it is provided correctly
        try:
            CS_default_configuration = self._config_space.get_default_configuration()
            parameters = []
            for parameter_name in self.__hyperparameter_names:
                parameters.append(CS_default_configuration.get(parameter_name))
            self.__default_configuration = Configuration(parameters, Configuration.Type.DEFAULT)
        except Exception as e:
            self.logger.error("Unable to load default Configuration: %s" % e)
            self.__default_configuration = None

    def get_hyperparameter_names(self) -> List[str]:
        return deepcopy(self.__hyperparameter_names)

    def _get_hyperparameter(self, hyperparameter_name: str) -> Hyperparameter:
        return self._config_space.get_hyperparameter(hyperparameter_name)
    
    def get_hyperparameter_type(self, hyperparameter_name: str) -> HyperparameterType:
        """
        Get the type of hyperparameter (feature from the model perspective) as enumeration.
        :param hyperparameter_name: String - name of Hyperparameter, whose type should be returned.
        :return: HyperparameterType
            Possible results:
            - 'HyperparameterType.NUMERICAL_FLOAT' and 'HyperparameterType.NUMERICAL_INTEGER' for numerical data.
            - 'HyperparameterType.CATEGORICAL_ORDINAL' and 'HyperparameterType.CATEGORICAL_NOMINAL' for categorical.
        """

        hyperparameter = self._get_hyperparameter(hyperparameter_name)
        h_type = None
        if isinstance(hyperparameter, UniformFloatHyperparameter):
            h_type = HyperparameterType.NUMERICAL_FLOAT
        elif isinstance(hyperparameter, UniformIntegerHyperparameter):
            h_type = HyperparameterType.NUMERICAL_INTEGER
        elif isinstance(hyperparameter, OrdinalHyperparameter):
            h_type = HyperparameterType.CATEGORICAL_ORDINAL
        elif isinstance(hyperparameter, CategoricalHyperparameter):
            h_type = HyperparameterType.CATEGORICAL_NOMINAL
        return h_type

    def get_hyperparameter_boundaries(self, hyperparameter_name):
        """
        This method is valid only for continuous hyperparameters (either int or float).
        Use 'get_hyperparameter_categories(hyperparameter_name)' for categorical hyperparameters instead.
        :param  hyperparameter_name: str. Name of hyperparameters to get boundaries of
        :return: lower_bound, upper_bound
        """
        hyperparameter = self._get_hyperparameter(hyperparameter_name)
        try:
            return hyperparameter.lower, hyperparameter.upper
        except AttributeError:
            self.logger.error(f"Hyperparameter {type(hyperparameter)} has no lower and upper bounds.")

    def get_hyperparameter_categories(self, hyperparameter_name):
        """
        This method is valid only for categorical hyperparameters.
        Use 'get_hyperparameter_boundaries(hyperparameter_name)' for continuous hyperparameters instead.
        :param  hyperparameter_name: str. Name of hyperparameters to get choices of
        :return: List of choices
        """
        hyperparameter = self._get_hyperparameter(hyperparameter_name)
        if isinstance(hyperparameter, CategoricalHyperparameter):
            return deepcopy(hyperparameter.choices)
        elif isinstance(hyperparameter, OrdinalHyperparameter):
            return deepcopy(hyperparameter.sequence)
        else:
            raise TypeError(f"Hyperparameter {type(hyperparameter)} has no discrete choices.")
    
    def get_default_configuration(self):
        return self.__default_configuration
    
    def set_default_configuration(self, default_configuration: Configuration):
        self.__default_configuration = default_configuration

    def get_conditions_for_hyperparameter(self, hyperparameter_name):
        conditions = {}
        for condition in self._config_space.get_parent_conditions_of(hyperparameter_name):
            conditions[condition.parent.name] = []
            if isinstance(condition, InCondition):
                conditions[condition.parent.name].append(condition.values)
            elif isinstance(condition, EqualsCondition):
                conditions[condition.parent.name].append(condition.value)
        return conditions

    def get_search_space_size(self) -> float:
        """
        Calculate the number of possible Configurations (unique Hyperparameter combinations)
        in the defined Search Space.
        If Continuous Hyperparameters do exist in Search Space definition,
        the Search Space size assumed to be infinite.
        :return: float, number of unique Configurations in Search Space.
        """
        if self.search_space_size is not None:
            return self.search_space_size
        else:
            search_space_size = 1.0
            self.logger.warning("During Search Space size calculation, Hyperparameter Conditions are going to be "
                                "ignored for the sake of simplicity!")
            for h_name in self.get_hyperparameter_names():
                h_type = self.get_hyperparameter_type(h_name)

                if h_type is HyperparameterType.NUMERICAL_FLOAT:
                    search_space_size = float("inf")
                    self.logger.warning(f"Hyperparameter {h_name} has infinite number of possible values.")
                    break

                elif h_type is HyperparameterType.NUMERICAL_INTEGER:
                    lower, upper = self.get_hyperparameter_boundaries(h_name)
                    search_space_size *= upper - lower

                elif h_type in (HyperparameterType.CATEGORICAL_ORDINAL, HyperparameterType.CATEGORICAL_NOMINAL):
                    search_space_size *= len(self.get_hyperparameter_categories(h_name))

                else:
                    self.logger.warning(f"Hyperparameter {h_name} has unknown type: {h_type}.")
                    search_space_size = float("inf")
                    break
            if search_space_size == float("inf"):
                self.logger.warning(f"The Search Space size is set to be infinite. Some BRISE functionality may be disabled.")

            self.search_space_size = search_space_size
            return search_space_size

    def create_configuration(self, values: Union[None,  Dict[str, Union[str, float, int]]] = None,
                             vector: Union[None, np.ndarray] = None) -> Configuration:
        """
        Method that creates new BRISE Configuration using ConfigSpace notions of `vector` and `values`.
        If both, `vector` and `values` are provided - create from `vector`, ignore `values`.
        :param values: dict. Optional parameter. Should be set to get Configuration from pre-defined values
        :param vector: np.ndarray. Optional parameter. Should be set to get Configuration from set vector
        :return: sampled Configuration
        """
        try:
            if vector is not None:
                cs_vector = [None]*len(self.get_hyperparameter_names())
                for cs_idx, cs_param in enumerate(self._config_space.get_hyperparameter_names()):
                    for idx, param in enumerate(self.get_hyperparameter_names()):
                        if cs_param == param:
                            cs_vector[cs_idx] = vector[idx]
                cs_configuration = CSConfiguration(self._config_space, vector=cs_vector)
            elif values is not None:
                cs_configuration = CSConfiguration(self._config_space, values=values)
            else:
                raise TypeError("A new Configuration creation requires either parameter 'vector' or parameter 'values'.")
        except ForbiddenValueError as error:
            self.logger.error(f"Tried to sample forbidden configuration: {error}")
            raise error
        parameters = []
        for parameter_name in self.__hyperparameter_names:
            parameters.append(cs_configuration.get(parameter_name))
        return Configuration(parameters, Configuration.Type.FROM_SELECTOR)

    def sample_configuration(self) -> Configuration:
        """
        Samples random Configuration by delegating this process to ConfigSpace framework.
        (`Mersenne Twister pseudo-random generator is used as a core <https://docs.python.org/3/library/random.html>`_).
        :return: Configuration
        """
        configuration = self._config_space.sample_configuration()
        return Configuration([configuration.get(param_name) for param_name in self.__hyperparameter_names],
                             Configuration.Type.FROM_SELECTOR)

    def generate_searchspace_description(self):
        """
        This is a helper method, that is needed to generate a description 
        of a search space in a dictionary form
        :return: dict: search space description
        """
        search_space_description = {}
        boundaries = {}
        boundary = []
        for hyperparameter_name in self.get_hyperparameter_names():
            if self.get_hyperparameter_type(hyperparameter_name) is HyperparameterType.NUMERICAL_FLOAT or \
                self.get_hyperparameter_type(hyperparameter_name) is HyperparameterType.NUMERICAL_INTEGER:
                boundary = self.get_hyperparameter_boundaries(hyperparameter_name)
            else:
                boundary = self.get_hyperparameter_categories(hyperparameter_name)
            boundaries[hyperparameter_name] = boundary
        search_space_size = self.get_search_space_size()
        search_space_description["boundaries"] = boundaries
        search_space_description["size"] = "Infinity" if search_space_size == float("inf") else search_space_size
        return search_space_description

    def get_indexes(self, config: Configuration) -> List[Union[int, float]]:
        """
        Helper function to extract configuration from the searchspace in format of its indexes in this search space.
        :param config: Configuration.
        :return: List of parameter indexes.
        """
        hyperparameters = [self._get_hyperparameter(name) for name in self.get_hyperparameter_names()]
        indexes = []
        for idx, param in enumerate(config.parameters):
            if param is None:
                # 'None' values appear when a dependency
                # between parameters are violated and some of parameters are "disabled".
                indexes.append(-1)
            else:
                hp = hyperparameters[idx]
                if isinstance(hp, (CategoricalHyperparameter, OrdinalHyperparameter)):
                    choices = self.get_hyperparameter_categories(self.get_hyperparameter_names()[idx])
                    indexes.append(choices.index(param))
                elif isinstance(hp, (UniformIntegerHyperparameter, UniformFloatHyperparameter)):
                    lower, upper = self.get_hyperparameter_boundaries(self.get_hyperparameter_names()[idx])
                    indexes.append((param - lower) / (upper - lower))
                else:
                    raise TypeError(f"Unsupported hyperparameter {hp}.")
        return indexes
