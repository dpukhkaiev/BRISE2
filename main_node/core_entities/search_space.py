from __future__ import annotations

import pickle
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Dict, Iterable, List, Set, MutableMapping, Union, Tuple
import numpy as np
import pandas as pd

_CATEGORY = Union[str, int, float, bool]


class Hyperparameter(ABC):
    """
    The main building block of the Search Space.

    Using Hyperparameter(s), one could define Search Space as a combination of several Hyperparameters into a
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

    def __init__(self,
                 name: str,
                 level: int,
                 parent: Hyperparameter = None,
                 activation_category: _CATEGORY = None):
        self.name = name
        self.configuration_number = 0
        self.level = level  # level within the search space
        self.parent = parent
        self.type = None
        # TODO enable numerical values
        self.activation_category = activation_category  # category activating this parameter

    @abstractmethod
    def get_default(self) -> MutableMapping:
        """
        Get mapping of Hyperparameter name to its default value.
        :return: The MutableMapping of Hyperparameter name to corresponding default value.
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

    @abstractmethod
    def transform(self, value):
        """
        Transform a value between 0 and 1 to a corresponding Hyperparameter value.
        """
        pass

    def new_are_siblings(self, other: Hyperparameter) -> bool:
        """
            Check whether current Hyperparameter is within the same region as another Hyperparameter.
            :param other: Hyperparameter
            :return: boolean
        """
        return self.parent.__eq__(other.parent) and self.activation_category.__eq__(other.activation_category)

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
    def get_children(self) -> List[Hyperparameter]:
        raise TypeError("Child Hyperparameters are only available in Composite Hyperparameter type.")

    @abstractmethod
    def remove_children(self):
        raise TypeError("Child Hyperparameters are only available in Composite Hyperparameter type.")

    def get_type(self) -> str:
        return self.type

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

    def serialize(self, first, boundaries=None) -> Dict:
        """
        Serialize search space to mapping object, which could be later used to restore search space object.
        :return: Mapping
        """
        raise NotImplementedError


class CategoricalHyperparameter(Hyperparameter, ABC):
    """
    Currently only Categorical Hyperparameters could become Composite.
    """

    def __init__(self,
                 name: str,
                 level: int,
                 categories: Iterable[_CATEGORY],
                 default_value: _CATEGORY = None,
                 parent: Hyperparameter = None,
                 activation_category: _CATEGORY = None
                 ):
        super().__init__(name, level, parent, activation_category)

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
        if activation_category is not None:
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

    def get_children(self) -> List[Hyperparameter]:
        children: List[Hyperparameter] = []
        for region in list(self._categories.values()):
            for child in region:
                children.append(child)
        return children

    def remove_children(self):
        for category in self._categories:
            self._categories[category] = []

    def get_size(self) -> Union[int, np.inf]:
        accumulated_size = 0
        for children in self._categories.values():
            branch_size = 1
            for child in children:
                branch_size *= child.get_size()
            accumulated_size += branch_size
        return accumulated_size

    def get_default(self) -> MutableMapping:
        default_value = OrderedDict({self.name: self._default_value})
        return default_value

    def __repr__(self):
        represent = f"{self.__class__.__name__} '{self.name}'."
        represent += f"\n├ Default category: '{self._default_value}'."
        represent += "\n├ Categories:"
        for category in self._categories:
            represent += f"\n├  {category}:"
            for child in self._categories[category]:
                represent += "\n├+   " + "\n├    ".join(str(child).split("\n"))
        return represent

    def serialize(self, first, boundaries=None) -> Dict:
        if first is True:
            self.first = True
            boundaries = {}
            parameters = []
            root_parameters_list = []
        else:
            self.first = False

        first = False
        categories_description = []
        for category, children in self._categories.items():
            categories_description.append(category)
            if self.first:
                parameters.append({"RootParameter": category})
                root_parameters_list.append(category)
        if not self.first:
            boundaries[self.name] = categories_description
        for category, children in self._categories.items():
            if self.first:
                boundaries[self.name] = [category]
            for child in children:
                boundaries = child.serialize(first, boundaries)
            if self.first:
                for index in range(0, len(parameters)):
                    if parameters[index]["RootParameter"] == category:
                        parameters[index]["Boundaries"] = boundaries
                        boundaries = {}

        if self.first:
            search_space_size = self.get_size()
            if search_space_size == np.inf:
                search_space_size = "Infinity"
            serialization = dict(
                size=search_space_size,
                name=self.name,
                boundaries=parameters,
                root_parameters_list=root_parameters_list
            )
            return serialization
        else:
            return boundaries

    def transform(self, value):
        categories = list(self._categories.keys())
        category_index = round(value * (len(categories) - 1))
        return categories[category_index]

    def __eq__(self, other):
        return super.__eq__(self, other)

    def __hash__(self):
        return super.__hash__(self)


class NumericHyperparameter(Hyperparameter, ABC):
    def __init__(self,
                 name: str,
                 level: int,
                 lower: Union[int, float],
                 upper: Union[int, float],
                 default_value: Union[int, float] = None,
                 parent: Hyperparameter = None,
                 activation_category: _CATEGORY = None):
        super().__init__(name, level, parent, activation_category)

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

    def get_children(self) -> List[Hyperparameter]:
        return []

    def remove_children(self):
        pass

    def get_default(self) -> MutableMapping:
        return OrderedDict({self.name: self._default_value})

    def get_upper(self):
        return self._upper

    def get_lower(self):
        return self._lower

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

    def __hash__(self):
        return super().__hash__(self)

    def serialize(self, first, boundaries=None) -> Dict:
        boundaries[self.name] = self._lower, self._upper
        return boundaries


class IntegerHyperparameter(NumericHyperparameter):

    def __init__(self,
                 name: str,
                 level: int,
                 lower: Union[int, float],
                 upper: Union[int, float],
                 default_value: Union[int, float] = None,
                 parent: Hyperparameter = None,
                 activation_category: _CATEGORY = None):
        default_value = default_value or (upper - lower) // 2
        super().__init__(name, level, int(lower), int(upper), default_value, parent, activation_category)
        self.type = "Integer"

    def get_size(self) -> Union[int, np.inf]:
        return self._upper - self._lower

    def transform(self, value) -> int:
        return round(self._lower + value*(self._upper - self._lower))

    def __eq__(self, other):
        return super.__eq__(self, other)

    def __hash__(self):
        return super.__hash__(self)


class FloatHyperparameter(NumericHyperparameter):

    def __init__(self,
                 name: str,
                 level: int,
                 lower: Union[int, float],
                 upper: Union[int, float],
                 default_value: Union[int, float] = None,
                 parent: Hyperparameter = None,
                 activation_category: _CATEGORY = None):
        default_value = default_value or (upper - lower) / 2
        super().__init__(name, level, float(lower), float(upper), default_value, parent, activation_category)
        self.type = "Float"

    def get_size(self) -> Union[int, np.inf]:
        return np.inf

    def transform(self, value) -> float:
        return self._lower + value*(self._upper - self._lower)

    def __eq__(self, other):
        return super().__eq__(other)

    def __hash__(self):
        return super.__hash__(self)


class OrdinalHyperparameter(CategoricalHyperparameter):
    def __init__(self,
                 name: str,
                 level: int,
                 categories: Iterable[_CATEGORY],
                 default_value: _CATEGORY = None,
                 parent: Hyperparameter = None,
                 activation_category: _CATEGORY = None
                 ):
        super().__init__(name, level, categories, default_value, parent, activation_category)
        self.type = "Ordinal"

    def __eq__(self, other: OrdinalHyperparameter):
        if type(other) is OrdinalHyperparameter:
            result = super().__eq__(other)
            if result and not (isinstance(other, OrdinalHyperparameter)
                               or self._default_value != other._default_value
                               or self._categories != other._categories):
                result = False
            return result
        else:
            return False

    def __hash__(self):
        return super.__hash__(self)


class NominalHyperparameter(CategoricalHyperparameter):
    def __init__(self,
                 name: str,
                 level: int,
                 categories: Iterable[_CATEGORY],
                 default_value: _CATEGORY = None,
                 parent: Hyperparameter = None,
                 activation_category: _CATEGORY = None
                 ):
        super().__init__(name, level, categories, default_value, parent, activation_category)
        self.type = "Nominal"

    def __eq__(self, other: NominalHyperparameter):
        if type(other) is NominalHyperparameter:
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
        else:
            return False

    def __hash__(self):
        return super.__hash__(self)


class SearchSpace:
    def __init__(self, h: dict):
        self.is_flat = False
        self.hierarchical_view = self.initialize_hierarchical_view(h)
        self.flat_view = self.initialize_flat_view()
        self.number_of_levels = self.__get_number_of_levels()

        if "Flat" in h["Structure"].keys():
            self.is_flat = True
            self.search_space_description = self.flat_view
        else:
            self.search_space_description = self.hierarchical_view

        self._size = self.__get_size()

        self.current_level: List[Hyperparameter] = []
        self.current_level.append(self.search_space_description)
        self.next_level()

        self.regions = []
        while len(self.current_level) > 0:
            regions = self.get_regions_on_current_level()
            for r in regions:
                self.regions.append(r)
            self.next_level()

        self.reset_level()

        self.hp_names = sum([[hp.name for hp in r]for r in self.regions], [])

    def reset_level(self):
        self.current_level.append(self.search_space_description)
        self.next_level()

    def next_level(self):
        children: List[Hyperparameter] = []
        for h in self.current_level:
            children.extend(h.get_children())
        self.current_level = children
        return self.current_level

    def get_regions_on_current_level(self) -> Set[Tuple[Hyperparameter]]:
        regions: Set[Tuple[Hyperparameter]] = set()

        for h in self.current_level:
            region = tuple(filter(lambda x: h.new_are_siblings(x), self.current_level))  # list of relevant parameters
            regions.add(region)

        return regions

    def activate_regions(self, parent: pd.DataFrame) -> Set[Tuple[Hyperparameter]]:
        parent = parent.drop(columns=parent.columns.difference(self.hp_names))
        available_regions = self.get_regions_on_current_level()
        activated_regions = set()
        for r in available_regions:
            for hp in r:
                for p in parent.to_numpy().flatten():
                    if type(p) is str:  # TODO: only for categorical parameters. check if top-level features do not influence it
                        if hp.activation_category in p:
                            activated_regions.add(r)
        return activated_regions

    def serialize(self) -> Dict:
        # TODO test
        serialized_search_space_description = self.search_space_description.serialize(True)
        return serialized_search_space_description

    def flatten(self, h: Hyperparameter):
        """
         A recursive method, which constructs a flat representation of the search space.
         :param h: hierarchical representation of the search space
         :return: flattened representation of the search space
         """
        flattened_search_space = []
        if h.get_type() in ("Nominal", "Ordinal"):
            children = h.get_children()
            for child in children:
                flattened_search_space += self.flatten(child)
            if h.name != "root":
                flattened_search_space.append(h)
        else:
            flattened_search_space.append(h)

        return flattened_search_space

    @property
    def size(self):
        return self._size

    def __get_number_of_levels(self) -> int:
        flattened_parameters = self.flatten(self.hierarchical_view)
        return max([hp.level for hp in flattened_parameters]) + 1  # levels start with 0

    def __get_size(self) -> Union[int, np.inf]:
        size = 0
        flattened_parameters = self.flatten(self.hierarchical_view)
        for hp in flattened_parameters:
            if hp.get_type() in ("Nominal", "Ordinal"):
                size += len(hp.categories)
            elif hp.get_type() == "Integer":
                size += hp.get_upper() - hp.get_lower()
            else:
                return np.inf
        return size

    def initialize_hierarchical_view(self, hyperparameter_description: dict) -> Hyperparameter:
        """
        A recursive method whose intent is to create a hierarchical search space representation from the description.
        :param hyperparameter_description: search space parameters description in json format.
        :return: Hyperparameter object.
        """
        root = NominalHyperparameter(name="root", level=-1, categories=["root"], default_value="root")

        for name in hyperparameter_description.keys():
            if name == "Structure":
                continue
            h = self._inner_init(hyperparameter_description[name], name, root, "root")
            root.add_child_hyperparameter(h)

        return root

    def initialize_flat_view(self) -> Hyperparameter:
        root = NominalHyperparameter(name="root", level=-1, categories=["root"], default_value="root")
        from copy import deepcopy
        flattened_parameters = self.flatten(self.hierarchical_view)
        # find unique names set([p.name for p in flattened_parameters])
        unique_parameter_names = set([p.name for p in flattened_parameters])
        for hp in flattened_parameters:
            hp = deepcopy(hp)
            if hp.name in unique_parameter_names:
                root.add_child_hyperparameter(hp, activation_category="root")
                hp.activation_category = "root"
                hp.parent = root
                hp.remove_children()
                unique_parameter_names.remove(hp.name)

        return root

    def _inner_init(self, hyperparameter_description: dict,
                    name: str,
                    parent: Hyperparameter = None,
                    activation_category: _CATEGORY = None) -> Hyperparameter:
        h_name: str = name
        h_type: str = hyperparameter_description["Type"]
        level: int = hyperparameter_description["Level"]

        default_value = hyperparameter_description["Default"]
        # TODO rethink modeling of the default configuration. At the moment DCH can overwrite this value

        if h_type in ("NominalHyperparameter", "OrdinalHyperparameter"):
            categories: List[_CATEGORY] = hyperparameter_description["Categories"]

            if h_type == "NominalHyperparameter":
                h = NominalHyperparameter(name=h_name,
                                          level=level,
                                          categories=categories,
                                          default_value=default_value,
                                          parent=parent,
                                          activation_category=activation_category)
            else:
                h = OrdinalHyperparameter(name=h_name,
                                          level=level,
                                          categories=categories,
                                          default_value=default_value,
                                          parent=parent,
                                          activation_category=activation_category)

            # declared children for each category
            for c in categories:
                # derive category name from the absolute path
                relative_name = c.split(".")[-1]
                for hp in hyperparameter_description[relative_name].keys():
                    if hp != "Type":
                        child = self._inner_init(hyperparameter_description[relative_name][hp], hp, h, c)
                        h.add_child_hyperparameter(child, c)

        elif h_type in ("IntegerHyperparameter", "FloatHyperparameter"):
            lower_bound = hyperparameter_description["Lower"]
            upper_bound = hyperparameter_description["Upper"]
            if h_type == "IntegerHyperparameter":
                h = IntegerHyperparameter(name=h_name,
                                          level=level,
                                          lower=lower_bound,
                                          upper=upper_bound,
                                          default_value=default_value,
                                          parent=parent,
                                          activation_category=activation_category)
            else:
                h = FloatHyperparameter(name=h_name,
                                        level=level,
                                        lower=lower_bound,
                                        upper=upper_bound,
                                        default_value=default_value,
                                        parent=parent,
                                        activation_category=activation_category)

        else:
            import logging
            logging.debug(f"{hyperparameter_description}")
            raise TypeError(f"Hyperparameter {h_name} has unknown type: {h_type}.")
        return h

    def transform_flat_parameters_to_hierarchic(self, parameters: MutableMapping) -> MutableMapping:
        """
        Constructs a valid hierarchic configuration from a flattened configuration.
        """
        self.search_space_description = self.hierarchical_view
        self.reset_level()

        valid_parameters = {}

        activated_regions = self.get_regions_on_current_level()
        while len(activated_regions) > 0:
            self.next_level()
            next_activated_regions: Set[Tuple[Hyperparameter]] = set()
            for region in activated_regions:
                for hp in region:
                    valid_parameters[hp.name] = parameters[hp.name]

                    valid_parameters_series = pd.Series(valid_parameters.values(), valid_parameters.keys())
                    valid_parameters_df = pd.DataFrame(columns=valid_parameters_series.index)
                    valid_parameters_df.loc[0] = valid_parameters_series.values

                    if len(next_activated_regions) == 0:
                        next_activated_regions = self.activate_regions(valid_parameters_df)
                    else:
                        next_activated_regions.update(self.activate_regions(valid_parameters_df))
                activated_regions = next_activated_regions

        self.search_space_description = self.flat_view
        self.reset_level()
        return valid_parameters

################
# Auxiliary methods
################


def get_search_space_record(search_space: SearchSpace, experiment_id: str) -> Dict:
    record = {
        "Exp_unique_ID": experiment_id,
        "Search_space_size": search_space.size,
        "SearchspaceObject": pickle.dumps(search_space)
    }
    return record
