from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Union, List, Iterable, MutableMapping
from collections import OrderedDict

import numpy as np

_CATEGORY = Union[str, int, float, bool]


class Hyperparameter(ABC):
    """
    The fundamental entity of the Search Space.

    Using Hyperparameter(s), one could define Search Space as a combination of several Hyperparameters into
    tree-like structure with 'activation' dependencies.

    Tree-like structure should be defined using Composition of Hyperparameters, based on activation values.
    Activation value is a specific value (or list of values) of Hyperparameter taking which,
    parent Hyperparameter exposes it's child (or several children) Hyperparameter(s).

    The definition of access of Search Space started from the tree root as Composite Hyperparameter.
    One could also access specific branch of even a leaf of the defined Search Space, abstracting from
    the entire, parent Search Space.

    Possible relationships between Hyperparameters in defined structure:

        - Child-parent relations.
        Some specific values of Hyperparameters could require defining other, children Hyperparameters.
        It defines the shape of Search space as a tree.

            Child-parent relations currently defined only for Categorical Hyperparameters
             as an activation of Hyperparameter, based on specific category.
            Example: Categorical Hyperparameter "metaheuristic" could take three possible values (categories),
            each of which defines own children:
            - "genetic algorithm" category defines:
                - Integer Hyperparameter 'population_size';
                - Integer Hyperparameter 'offspring_population_size';
                - Nominal Hyperparameter 'mutation_type' (which is also a categorical hyperparameter);
                - etc...
            - "evolutionary strategy" category defines:
                - Integer Hyperparameter 'mu';
                - Integer Hyperparameter 'lambda';
                - Nominal Hyperparameter 'elitist';
                - etc...
            TODO: Support of child-parent relationship for Numeric hyperparameters.
            (Children are activated if Numeric Hyperparameter value is in specific boundaries).

            It could be done by encapsulating "activation" logic for each type of Hyperparameters to own type and
            composition logic into separate class. Currently Categorical Hyperparameter and composition logic are
            bounded.
    """

    def __init__(self, name: str):
        self.name = name

    #   --- Set of methods to operate with Hyperparameter values
    def validate(self, values: MutableMapping, recursive: bool) -> bool:
        """
        Validates if hyperparameter 'values' are valid in Search Space by ensuring that:
            1. Current Hyperparameter is defined in 'values' (the name is present).
            2. Hyperparameter value is not violated (done by specific type of Hyperparameter by itself).
            3. 'values' is valid for all "activated" children (done by Composition logic).

        :param values: The MutableMapping of Hyperparameter names to corresponding values.
        :param recursive: Boolean flag, whether to call "validate" also on all activated children.
        :returns: bool True if 'values' are valid.
        """
        return self.name in values

    @abstractmethod
    def generate(self, values: MutableMapping) -> None:
        """
        Take 'values', a MutableMapping from hyperparameter names to their values
         and extend it in following order:
            1. If current Hyperparameter is not in 'values':
             pick a random value for Hyperparameter (uniformly), modify Mapping adding key:value to 'values'.
             TODO: A logic of random sampling could be encapsulated to support more sophisticated sampling then uniform.
            2. If current Hyperparameter is in 'values':
            forward generate call to all "activated" children.

        :param values: The MutableMapping of Hyperparameter names to corresponding values.
        """
        pass

    @abstractmethod
    def generate_default(self) -> MutableMapping:
        """
        Generate hyperparameters set out of default values recursively.
        :return: The MutableMapping of Hyperparameter names to corresponding default values.
        """

    @abstractmethod
    def describe(self, values: MutableMapping) -> MutableMapping[str, MutableMapping[str, Union[Hyperparameter, list]]]:
        """
        Return description of each available hyperparameters as a MutableMapping.

        Example:
        {
            "hyperparameter1 name": {
                    "hyperparameter": Hyperparameter object
                    "boundaries": [lower, upper] if Hyperparameter is NumericHyperparameter
                    "categories": [cat1, ... catN] if Categorical is NumericHyperparameter
            },
            "hyperparameter2 name": {
                    "hyperparameter": Hyperparameter object
                    "boundaries": [lower, upper] if Hyperparameter is NumericHyperparameter
                    "categories": [cat1, ... catN] if Categorical is NumericHyperparameter
            }
            ...
        }
        """
        pass

    @abstractmethod
    def get_size(self) -> Union[int, float('inf')]:
        """
        Return size of Search Space.
        It will be calculated as all possible, unique and valid combinations of Hyperparameters,
         available in current Search Space.
        Note, by definition, numeric Float Hyperparameters have infinite size.
        :return: Union[int, float('inf')]
        """
        pass

    def are_siblings(self, base_values: MutableMapping, target_values: MutableMapping) -> bool:
        """
        Analyse whether hyperparameter values base_values
        form a sub-feature-tree of target_values hyperparameter values.

        Probably, the selected name for this method is not the best in terms of reflecting internal functionality,
        but I can not derive a better one yet...

        :param base_values: MutableMapping
        :param target_values: MutableMapping
        :return: boolean
        """
        # by default, leaf hyperparameters are siblings, the difference could be only in composite (categorical)
        return True

    #   --- Set of methods to operate the structure of the Search Space
    @abstractmethod
    def add_child_hyperparameter(self, other: Hyperparameter,
                                 activation_categories: Iterable[_CATEGORY]) -> Hyperparameter:
        """
        Add child Hyperparameter, that will be activated if parent Hyperparameter was assigned to one of
        activation categories.
        :param other: Hyperparameter
        :param activation_categories: list of activation categories, under which other will be accessible.
        :return:
        """
        raise TypeError("Child Hyperparameters are only available in Composite Hyperparameter type.")

    @abstractmethod
    def get_child_hyperparameter(self, name: str) -> Union[Hyperparameter, None]:
        raise TypeError("Child Hyperparameters are only available in Composite Hyperparameter type.")

    def __eq__(self, other: Hyperparameter):
        """
        Check if current Hyperparameter is the same as other.
        For composite hyperparameters call should be forwarded to every child.
        :param other: Hyperparameter
        :return: bool
        """
        return self.name == other.name


class CategoricalHyperparameter(Hyperparameter, ABC):
    """
    Currently only Categorical Hyperparameters could become Composite.
    """

    def __init__(self,
                 name: str,
                 categories: Iterable[_CATEGORY],
                 default_value: _CATEGORY = None):
        super().__init__(name)

        # Each category could 'activate' a children, so list of activated children is 'behind' each category.
        self._categories: MutableMapping[_CATEGORY, List[Hyperparameter]] = OrderedDict({cat: [] for cat in categories})

        self._default_value = default_value or list(self._categories)[len(self._categories) // 2]

    @property
    def categories(self):
        return tuple(self._categories.keys())

    def add_child_hyperparameter(self,
                                 other: Hyperparameter,
                                 activation_category: _CATEGORY = None
                                 ) -> Hyperparameter:

        # TODO: check for possible collisions in hyperparameter names
        #  (could cause unexpected behavior in generate, describe)
        if activation_category:
            self._add_to_category(activation_category, other)
        else:
            for category in self._categories:
                self._add_to_category(category, other)
        return self

    def _add_to_category(self, category: _CATEGORY, other: Hyperparameter):
        if category not in self._categories:
            raise ValueError(f"{self.name}: category {category} does not exist.")
        elif other in self._categories[category]:
            raise ValueError(f"{self.name}: Hyperparameter {other} was already added as child for {category} category.")
        else:
            self._categories[category].append(other)

    def get_child_hyperparameter(self, name: str) -> Union[Hyperparameter, None]:
        for children in self._categories.values():
            for child in children:
                if child.name == name:
                    return child

    def get_size(self) -> Union[int, float('inf')]:
        accumulated_size = 0
        for children in self._categories.values():
            branch_size = 1
            for child in children:
                branch_size *= child.get_size()
            accumulated_size += branch_size
        return accumulated_size

    def validate(self, values: MutableMapping, recursive: bool) -> bool:
        is_valid = super().validate(values, recursive)
        if not is_valid or values[self.name] not in self._categories:
            is_valid = False
        else:
            # now it is time to ask 'activated' children to validate
            if recursive:
                for child in self._categories[values[self.name]]:
                    is_valid = is_valid and child.validate(values, recursive)
                    if not is_valid:
                        break

        return is_valid

    def generate(self, values: MutableMapping) -> None:
        # if this hyperparameter is not in hyperparameters set already - add it
        # in other case - forwarding request to each 'activated' children.
        if self.name not in values:
            categories = list(self._categories.keys())
            # np.random.choice converts python primitive types 'int' and 'float' to np.int64 and np.float64 -_-
            values[self.name] = categories[np.random.randint(len(categories))]
        else:
            for child in self._categories[values[self.name]]:
                child.generate(values)

    def generate_default(self) -> MutableMapping:
        parent_values = OrderedDict({self.name: self._default_value})
        for child in self._categories[self._default_value]:
            child_values = child.generate_default()
            if any((ch in parent_values.keys() for ch in child_values.keys())):
                raise ValueError(f"Parent and Child hyperparameters names intersect: {parent_values}, {child_values}")
            parent_values.update(child_values)
        return parent_values

    def describe(self, values: MutableMapping) -> MutableMapping[str, MutableMapping[str, Union[Hyperparameter, list]]]:
        description = OrderedDict()
        if self.name in values:
            description[self.name] = {"hyperparameter": self, "categories": list(self._categories.keys())}
            for child in self._categories[values[self.name]]:
                description.update(child.describe(values))
        return description

    def are_siblings(self, base_values: MutableMapping, target_values: MutableMapping) -> bool:
        result = []
        if self.name in base_values:
            if base_values.get(self.name) == target_values.get(self.name):
                for child in self._categories[base_values[self.name]]:
                    result.append(child.are_siblings(base_values, target_values))
            else:
                result.append(False)
        return all(result)

    def __repr__(self):
        represent = f"{self.__class__.__name__} '{self.name}'."
        represent += f"\n├ Default category: '{self._default_value}'."
        represent += f"\n├ Categories:"
        for category in self._categories:
            represent += f"\n├  {category}:"
            for child in self._categories[category]:
                represent += "\n├+   " + "\n├    ".join(str(child).split("\n"))
        return represent


class NumericHyperparameter(Hyperparameter, ABC):
    def __init__(self,
                 name: str,
                 lower: Union[int, float],
                 upper: Union[int, float],
                 default_value: Union[int, float] = None):
        super().__init__(name)

        self._lower = lower
        self._upper = upper
        self._default_value = default_value

        if self._upper < self._lower:
            raise ValueError(f"{self.name}: Upper boundary ({self._upper}) is higher than lower ({self._lower}).")
        if not self._lower <= self._default_value <= self._upper:
            raise ValueError(f"{self.name}: Provided default value ({self._default_value}) is not within "
                             f"lower ({self._lower}) and upper ({self._upper}) boundaries.")

    def add_child_hyperparameter(self, other: Hyperparameter,
                                 activation_categories: Iterable[Union[str, int, float]]) -> Hyperparameter:
        raise TypeError("Child Hyperparameters are only available in Composite Hyperparameter type.")

    def get_child_hyperparameter(self, name: str) -> Union[Hyperparameter, None]:
        raise TypeError("Child Hyperparameters are only available in Composite Hyperparameter type.")

    def generate_default(self) -> MutableMapping:
        return OrderedDict({self.name: self._default_value})

    def validate(self, values: MutableMapping, recursive: bool) -> bool:
        result = super().validate(values, recursive)
        if result is True:
            result = self._lower <= values[self.name] <= self._upper
        return result

    def describe(self, values: MutableMapping) -> MutableMapping[str, MutableMapping[str, Union[Hyperparameter, list]]]:
        description = OrderedDict()
        if self.name in values:
            description[self.name] = OrderedDict({"hyperparameter": self, "boundaries": [self._lower, self._upper]})
        return description

    def __repr__(self):
        represent = f"{self.__class__.__name__} '{self.name}'"
        represent += f"\n| Lower boundary: {self._lower}, upper boundary: {self._upper}."
        represent += f"\n| Default value: {self._default_value}."
        return represent

    def __eq__(self, other: NumericHyperparameter):
        result = super().__eq__(other)
        if not isinstance(other, NumericHyperparameter) \
                or self._lower != other._lower \
                or self._upper != other._upper \
                or self._default_value != other._default_value:
            result = False
        return result


class IntegerHyperparameter(NumericHyperparameter):

    def __init__(self,
                 name: str,
                 lower: Union[int, float],
                 upper: Union[int, float],
                 default_value: Union[int, float] = None):
        default_value = default_value or (upper - lower) // 2
        super().__init__(name, int(lower), int(upper), default_value)

    def generate(self, values: MutableMapping) -> None:
        if self.name not in values:
            values[self.name] = np.random.randint(self._lower, self._upper + 1)

    def validate(self, values: MutableMapping, recursive: bool) -> bool:
        return super().validate(values, recursive) and isinstance(values[self.name], int)

    def get_size(self) -> Union[int, float('inf')]:
        return self._upper - self._lower


class FloatHyperparameter(NumericHyperparameter):

    def __init__(self,
                 name: str,
                 lower: Union[int, float],
                 upper: Union[int, float],
                 default_value: Union[int, float] = None):
        default_value = default_value or (upper - lower) / 2
        super().__init__(name, float(lower), float(upper), default_value)

    def generate(self, values: MutableMapping) -> None:
        if self.name not in values:
            values[self.name] = np.random.uniform(low=self._lower, high=self._upper)

    def validate(self, values: MutableMapping, recursive: bool) -> bool:
        return super().validate(values, recursive) and isinstance(values[self.name], float)

    def get_size(self) -> Union[int, float('inf')]:
        return float('inf')


class OrdinalHyperparameter(CategoricalHyperparameter):
    def __eq__(self, other: OrdinalHyperparameter):
        result = super().__eq__(other)
        if result and not (isinstance(other, OrdinalHyperparameter)
                           or self._default_value != other._default_value
                           or self._categories != other._categories):
            result = False
        return result


class NominalHyperparameter(CategoricalHyperparameter):
    def __eq__(self, other: NominalHyperparameter):
        result = super().__eq__(other)
        if result and not (isinstance(other, NominalHyperparameter)
                           or self._default_value != other._default_value
                           or self._categories.keys() != other._categories.keys()):
            result = False
        elif result:
            for cat in self._categories.keys():
                if cat not in other._categories or self._categories[cat] != other._categories[cat]:
                    result = False
                    break
        return result


def from_json(file: str) -> Hyperparameter:
    def _build(hyperparameter_description: dict) -> Hyperparameter:
        h_name: str = hyperparameter_description["name"]
        h_type: str = hyperparameter_description["type"]
        default_value = hyperparameter_description.get("default", None)

        if h_type in ("NominalHyperparameter", "OrdinalHyperparameter"):
            categories_desc: List[MutableMapping[str, _CATEGORY]] = hyperparameter_description["categories"]
            categories: List[_CATEGORY] = [category["category"] for category in categories_desc]
            shared_children_desc = hyperparameter_description.get("children", None)

            if h_type == "NominalHyperparameter":
                h = NominalHyperparameter(name=h_name, categories=categories, default_value=default_value)
            else:
                h = OrdinalHyperparameter(name=h_name, categories=categories, default_value=default_value)

            # declared shared children
            if shared_children_desc:
                for shared_child_desc in shared_children_desc:
                    sh_child = _build(shared_child_desc)
                    h.add_child_hyperparameter(sh_child)

            # declared children for each category
            for category in categories_desc:
                if "children" in category:
                    for child_des in category["children"]:
                        child = _build(child_des)
                        h.add_child_hyperparameter(child, activation_category=category["category"])

        elif h_type in ("IntegerHyperparameter", "FloatHyperparameter"):
            lower_bound = hyperparameter_description["lower"]
            upper_bound = hyperparameter_description["upper"]
            if h_type == "IntegerHyperparameter":
                h = IntegerHyperparameter(name=h_name, lower=lower_bound, upper=upper_bound,
                                          default_value=default_value)
            else:
                h = FloatHyperparameter(name=h_name, lower=lower_bound, upper=upper_bound, default_value=default_value)

        else:
            import logging
            logging.debug(f"{hyperparameter_description}")
            raise TypeError(f"Hyperparameter {h_name} has unknown type: {h_type}.")

        return h

    import json
    # TODO Add validation and schema
    with open(file) as source:
        description = json.load(source)
    return _build(description)

# --- OLD search space

from enum import Enum
from ConfigSpace.configuration_space import Configuration as CSConfiguration
from ConfigSpace import InCondition, EqualsCondition
from ConfigSpace.read_and_write import json as CSjson
from ConfigSpace.exceptions import ForbiddenValueError
from ConfigSpace.hyperparameters import Hyperparameter
from ConfigSpace import UniformIntegerHyperparameter, UniformFloatHyperparameter, OrdinalHyperparameter, CategoricalHyperparameter


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
        self.__hyperparameter_names = self._config_space.get_hyperparameter_names()

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

        # todo: its a work-around similar we had in original hh
        if cs_configuration.get("low level heuristic", "") == "jMetalPy.EvolutionStrategy":
            if cs_configuration['py.ES|lambda_'] < cs_configuration['py.ES|mu']:
                self.logger.warning(f"Hyperparameter 'lambda_' was altered from {cs_configuration['py.ES|lambda_']} to"
                                        f" {cs_configuration['py.ES|mu']}!")
                cs_configuration['py.ES|lambda_'] = cs_configuration['py.ES|mu']
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
        # todo: its a work-around similar we had in original hh
        if configuration.get("low level heuristic", "") == "jMetalPy.EvolutionStrategy":
            if configuration['py.ES|lambda_'] < configuration['py.ES|mu']:
                self.logger.warning(f"Hyperparameter 'lambda_' was altered from {configuration['py.ES|lambda_']} to"
                                        f" {configuration['py.ES|mu']}!")
                configuration['py.ES|lambda_'] = configuration['py.ES|mu']
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