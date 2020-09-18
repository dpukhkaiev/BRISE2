from __future__ import annotations
import pickle
from abc import ABC, abstractmethod
from typing import Union, List, Iterable, MutableMapping, Dict
from collections import OrderedDict
from selection.selection_algorithms import get_selector
from selection.selection_algorithm_abs import SelectionAlgorithm

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
            each defining its own children:
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
            composition logic into a separate class. Currently Categorical Hyperparameters and composition logic are
            bounded.
    """

    def __init__(self, name: str):
        self.name = name
        self.configuration_number = 0

    #   --- Set of methods to operate with Hyperparameter values
    def validate(self, values: MutableMapping, is_recursive: bool) -> bool:
        """
        Validates if hyperparameter 'values' are valid in Search Space by ensuring that:
            1. Current Hyperparameter is defined in 'values' (the name is present).
            2. Hyperparameter value is not violated (done by specific type of Hyperparameter by itself).
            3. 'values' is valid for all "activated" children (done by Composition logic).

        :param values: The MutableMapping of Hyperparameter names to corresponding values.
        :param is_recursive: Boolean flag, whether to call "validate" also on all activated children.
        :returns: bool True if 'values' are valid.
        """
        return self.name in values

    @abstractmethod
    def generate(self, values: MutableMapping) -> None:
        """
        Take 'values', a MutableMapping from hyperparameter names to their values
         and extend it in following order:
            1. If current Hyperparameter is not in 'values':
             pick a random value for Hyperparameter according to a user-defined selection algorithm,
             modify Mapping adding key:value to 'values'.
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
                    "boundaries": [lower, upper] if Hyperparameter is Numeric
                    "categories": [cat1, ... catN] if Hyperparameter is Categorical
            },
            "hyperparameter2 name": {
                    "hyperparameter": Hyperparameter object
                    "boundaries": [lower, upper] if Hyperparameter is Numeric
                    "categories": [cat1, ... catN] if Hyperparameter is Categorical
            }
            ...
        }
        """
        pass

    @abstractmethod
    def get_size(self) -> Union[int, np.inf]:
        """
        Return size of Search Space.
        It will be calculated as all possible, unique and valid combinations of Hyperparameters,
         available in current Search Space.
        Note, by definition, numeric Float Hyperparameters have infinite size.
        :return: Union[int, np.inf]
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

    def __hash__(self):
        return hash(self.name)

    def serialize(self) -> Dict:
        """
        Serialize search space to mapping object, which could be later used to restore search space object.
        :return: Mapping
        """
        raise NotImplemented()

    def update_selection_algorithm(self, selection_algorithm, dimensionality):
        self.dimensionality = dimensionality
        self.selection_algorithm = selection_algorithm

    def get_selection(self, length):
        value = self.selection_algorithm.get_value(self.dimensionality, self.configuration_number, length - 1)
        self.configuration_number += 1
        return value


class CategoricalHyperparameter(Hyperparameter, ABC):
    """
    Currently only Categorical Hyperparameters could become Composite.
    """

    def __init__(self,
                 name: str,
                 categories: Iterable[_CATEGORY],
                 default_value: _CATEGORY = None):
        super().__init__(name)

        # Each category could 'activate' children, so list of activated children is 'behind' each category.
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

    def get_size(self) -> Union[int, np.inf]:
        accumulated_size = 0
        for children in self._categories.values():
            branch_size = 1
            for child in children:
                branch_size *= child.get_size()
            accumulated_size += branch_size
        return accumulated_size

    def validate(self, values: MutableMapping, is_recursive: bool) -> bool:
        is_valid = super().validate(values, is_recursive)
        if not is_valid or values[self.name] not in self._categories:
            is_valid = False
        else:
            # now it is time to ask 'activated' children to validate
            if is_recursive:
                for child in self._categories[values[self.name]]:
                    is_valid = is_valid and child.validate(values, is_recursive)
                    if not is_valid:
                        break

        return is_valid

    def generate(self, values: MutableMapping) -> None:
        # if this hyperparameter is not in hyperparameters set already - add it
        # in other case - forwarding request to each 'activated' children.
        if self.name not in values:
            categories = list(self._categories.keys())
            # np.random.choice converts python primitive types 'int' and 'float' to np.int64 and np.float64 -_-
            value = self.get_selection(len(values))
            values[self.name] = categories[self.transform(value)]
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

    def serialize(self) -> Dict:
        categories_description = []
        for category, children in self._categories.items():
            cat_description = {
                "category": category,
                "children": [child.serialize() for child in children]
            }
            categories_description.append(cat_description)
        serialization = dict(
            name=self.name,
            type=type(self).__name__,
            categories=categories_description,
            default=self._default_value
        )

        return serialization
    
    def transform(self, value):
        categories = list(self._categories.keys())
        return round(value*(len(categories) - 1))


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

    def validate(self, values: MutableMapping, is_recursive: bool) -> bool:
        result = super().validate(values, is_recursive)
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

    def serialize(self) -> Dict:
        serialization = dict(
            name=self.name,
            type=type(self).__name__,
            lower=self._lower,
            upper=self._upper,
            default=self._default_value
        )
        return serialization


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
            value = self.get_selection(len(values))
            values[self.name] = self.transform(value)

    def validate(self, values: MutableMapping, is_recursive: bool) -> bool:
        return super().validate(values, is_recursive) and isinstance(values[self.name], int)

    def get_size(self) -> Union[int, np.inf]:
        return self._upper - self._lower
    
    def transform(self, value):
        return round(self._lower + value*(self._upper - self._lower))


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
            value = self.get_selection(len(values))
            values[self.name] = self.transform(value)

    def validate(self, values: MutableMapping, is_recursive: bool) -> bool:
        return super().validate(values, is_recursive) and isinstance(values[self.name], float)

    def get_size(self) -> Union[int, np.inf]:
        return np.inf
    
    def transform(self, value):
        return self._lower + value*(self._upper - self._lower)


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


################
# Auxiliary methods
################
def initialize_search_space(hyperparameter_description: dict, selection_algorithm: dict) -> Hyperparameter:
    """
    Auxiliary method of search space creation. The main intent is to avoid unnecessary selection algorithm
    object creations in the recursive method 'initialize_hyperparameter'
    :param hyperparameter_description: search space parameters description in json format.
    :param selection_algorithm: the selection algorithm description in json format.
    :return: search space object.
    """
    selector = get_selector(selection_algorithm)
    dimensionality = get_dimensionality(hyperparameter_description, 0) - 1
    h = initialize_hyperparameter(hyperparameter_description, selector, dimensionality)
    return h

def initialize_hyperparameter(hyperparameter_description: dict, selector: SelectionAlgorithm, dimensionality: int) -> Hyperparameter:
    """
    A recursive method which intent is to create search space object from the description.
    :param hyperparameter_description: search space parameters description in json format.
    :param selector: the selection algorithm object.
    :param dimensionality: the number of parameters in search space.
    :return: search space object.
    """
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
                sh_child = initialize_hyperparameter(shared_child_desc, selector, dimensionality) # Recursion
                h.add_child_hyperparameter(sh_child)

        # declared children for each category
        for category in categories_desc:
            if "children" in category:
                for child_des in category["children"]:
                    child = initialize_hyperparameter(child_des, selector, dimensionality) # Recursion
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
    h.update_selection_algorithm(selector, dimensionality)
    return h


def get_search_space_record(search_space: Hyperparameter, experiment_id: str) -> Dict:
    record = {
        "Exp_unique_ID": experiment_id,
        "Search_space_size": search_space.get_size(),
        "SearchspaceObject": pickle.dumps(search_space)
    }
    return record

def get_dimensionality(hyperparameter_description: Hyperparameter, dimensionality: int) -> int:
    """
    A recursive method which intent is to count the number of parameters in the search space.
    :param hyperparameter_description: search space parameters description in json format.
    :param dimensionality: the counter which is transferred between recursive calls.
    :return: number of counted hyperparameters
    """
    h_type: str = hyperparameter_description["type"]

    if h_type in ("NominalHyperparameter", "OrdinalHyperparameter"):
        categories_desc: List[MutableMapping[str, _CATEGORY]] = hyperparameter_description["categories"]
        shared_children_desc = hyperparameter_description.get("children", None)

        if shared_children_desc:
            for shared_child_desc in shared_children_desc:
                dimensionality = get_dimensionality(shared_child_desc, dimensionality) # Recursion

        for category in categories_desc:
            if "children" in category:
                for child_des in category["children"]:
                    dimensionality = get_dimensionality(child_des, dimensionality) # Recursion
    dimensionality += 1
    return dimensionality