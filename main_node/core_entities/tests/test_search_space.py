import json

import numpy as np
import pandas as pd
import pytest

from core_entities.search_space import (
    INACTIVE_CATEGORY, SEARCH_SPACE_PREFIX, FloatHyperparameter, IntegerHyperparameter, NominalHyperparameter,
    OrdinalHyperparameter, SearchSpace
)


class TestRegions:
    """
    Regions are collected into a set, whose iteration order differs between processes, while the
    position of a region within search_space.regions is persisted with every configuration and
    compared across experiments. The order must therefore be canonical, not a set iteration order.
    """

    def test_regions_are_ordered_by_level_and_activation_path(self, get_experiment):
        # test_case_15 has two regions on level 1 (N0.N01 and N0.N02) and two on level 2
        # (N1.N11 and O1.O11), so several regions compete for a position within their level
        _, search_space = get_experiment(15)

        assert [region[0].activation_category for region in search_space.regions] == [
            "root",
            "Context.SearchSpace.N0.N01",
            "Context.SearchSpace.N0.N02",
            "Context.SearchSpace.N0.N02.N1.N11",
            "Context.SearchSpace.N0.N02.O1.O11",
            "Context.SearchSpace.N0.N02.N1.N11.N2.N21",
        ]
        assert [region[0].level for region in search_space.regions] == [0, 1, 1, 2, 2, 3]

    def test_deeper_regions_never_precede_shallower_ones(self, get_experiment):
        # in test_case_16 the deepest region descends from N01, which is the second region of its
        # own level, so sorting by the activation path alone would lift it above its siblings
        _, search_space = get_experiment(16)

        assert [region[0].activation_category for region in search_space.regions] == [
            "root",
            "Context.SearchSpace.N0.N01",
            "Context.SearchSpace.N0.N02",
            "Context.SearchSpace.N0.N01.X.XA",
        ]
        assert [region[0].level for region in search_space.regions] == [0, 1, 1, 2]


class TestEqualWidthBins:
    """
    Sampling maps a value of [0, 1] to a category or an integer, so each of them must get an equal share of it.
    """

    @staticmethod
    def _counts(hyperparameter, resolution=10000):
        values = [hyperparameter.transform(v) for v in np.linspace(0, 1, resolution)]
        return pd.Series(values).value_counts(normalize=True).sort_index()

    def test_every_category_gets_an_equal_share(self):
        shares = self._counts(NominalHyperparameter("n", 0, list("abcde")))

        assert list(shares.index) == list("abcde")
        assert np.allclose(shares.values, 0.2, atol=0.01)

    def test_every_integer_gets_an_equal_share(self):
        shares = self._counts(IntegerHyperparameter("i", 0, 1, 10))

        assert list(shares.index) == list(range(1, 11))
        assert np.allclose(shares.values, 0.1, atol=0.01)

    def test_the_ends_of_the_range_map_to_the_bounds(self):
        integer = IntegerHyperparameter("i", 0, 3, 7, default_value=5)
        nominal = NominalHyperparameter("n", 0, ["x", "y", "z"])

        assert (integer.transform(0), integer.transform(1)) == (3, 7)
        assert (nominal.transform(0), nominal.transform(1)) == ("x", "z")


class TestDefaultValues:

    def test_declared_zero_default_is_kept(self):
        assert IntegerHyperparameter("i", 0, 0, 10, default_value=0).get_default()["i"] == 0
        assert NominalHyperparameter("n", 0, [0, 1, 2], default_value=0).get_default()["n"] == 0
        assert FloatHyperparameter("f", 0, 0.0, 1.0, default_value=0.0).get_default()["f"] == 0.0

    def test_missing_default_is_the_middle_of_the_bounds(self):
        assert IntegerHyperparameter("i", 0, 3, 7).get_default()["i"] == 5
        assert FloatHyperparameter("f", 0, 2.0, 4.0).get_default()["f"] == 3.0
        assert NominalHyperparameter("n", 0, ["x", "y", "z"]).get_default()["n"] == "y"


class TestInactiveValue:
    """
    A configuration holds only its active parameters. A parameter that is missing from it is represented by its
    inactive value: below the lower bound of a numeric parameter, a value that is none of the categories of a
    categorical one. The value is defined here only, and never stored in a configuration.
    """

    @pytest.mark.parametrize("hyperparameter_class", [NominalHyperparameter, OrdinalHyperparameter])
    def test_categorical_parameter_has_an_inactive_value_that_is_not_one_of_its_categories(self, hyperparameter_class):
        categories = [f"{SEARCH_SPACE_PREFIX}.N0.{name}" for name in ("A", "B", "C")]
        hyperparameter = hyperparameter_class(f"{SEARCH_SPACE_PREFIX}.N0", 0, categories)

        assert hyperparameter.inactive_value() not in hyperparameter.categories
        assert not hyperparameter.inactive_value().startswith(SEARCH_SPACE_PREFIX)

    def test_category_equal_to_the_inactive_value_is_rejected(self):
        nominal = NominalHyperparameter("n", 0, ["a", INACTIVE_CATEGORY])

        with pytest.raises(ValueError):
            nominal.inactive_value()

    @pytest.mark.parametrize("hyperparameter", [IntegerHyperparameter("i", 0, 3, 7), FloatHyperparameter("f", 0, 2.5, 4.5)])
    def test_numeric_parameter_gets_a_value_one_range_below_its_lower_bound(self, hyperparameter):
        # min-max scaling over the bounds therefore maps it to -1 (for a non-empty range)
        lower, upper = hyperparameter.get_lower(), hyperparameter.get_upper()

        assert hyperparameter.inactive_value() == lower - (upper - lower)
        assert type(hyperparameter.inactive_value()) is type(lower)

    def test_numeric_parameter_with_equal_bounds_gets_a_value_outside_them(self):
        assert IntegerHyperparameter("i", 0, 5, 5).inactive_value() < 5
        assert FloatHyperparameter("f", 0, 2.0, 2.0).inactive_value() < 2.0


class TestDescribeRegions:
    """
    describe_regions() is the one description of the search space that main-node sends to its clients: the regions of
    SearchSpace.regions, with every parameter's name, type, level, categories or bounds and inactive value.
    """

    def test_regions_are_described_in_the_order_of_search_space_regions(self, get_experiment):
        # test_case_16 has regions on two levels, and a nominal parameter (N0.N01.X) whose child is also called X
        _, search_space = get_experiment(16)

        regions = search_space.describe_regions()

        assert [region["ActivationCategory"] for region in regions] == [
            str(region[0].activation_category) for region in search_space.regions
        ]
        assert [[parameter["Name"] for parameter in region["Parameters"]] for region in regions] == [
            [hp.name for hp in region] for region in search_space.regions
        ]
        assert [parameter["Name"] for region in regions for parameter in region["Parameters"]] == search_space.hp_names

    def test_parameters_are_described_by_type_level_domain_and_inactive_value(self, get_experiment):
        _, search_space = get_experiment(16)

        parameters = {parameter["Name"]: parameter
                      for region in search_space.describe_regions() for parameter in region["Parameters"]}

        root = parameters["Context.SearchSpace.N0"]
        assert (root["Type"], root["Level"]) == ("NominalHyperparameter", 0)
        assert root["Categories"] == ["Context.SearchSpace.N0.N01", "Context.SearchSpace.N0.N02"]
        assert "Lower" not in root and "Upper" not in root
        assert root["Inactive"] == INACTIVE_CATEGORY

        nominal = parameters["Context.SearchSpace.N0.N01.X"]
        assert (nominal["Type"], nominal["Level"]) == ("NominalHyperparameter", 1)
        assert nominal["Categories"] == ["Context.SearchSpace.N0.N01.X.XA", "Context.SearchSpace.N0.N01.X.XB"]

        float_parameter = parameters["Context.SearchSpace.N0.N02.F1"]
        assert (float_parameter["Type"], float_parameter["Level"]) == ("FloatHyperparameter", 1)
        assert (float_parameter["Lower"], float_parameter["Upper"]) == (0.0, 50.0)
        assert "Categories" not in float_parameter
        assert float_parameter["Inactive"] == -50.0

        nested = parameters["Context.SearchSpace.N0.N01.X.XA.X"]
        assert nested["Level"] == 2
        assert (nested["Lower"], nested["Upper"]) == (0.0, 10.0)
        assert nested["Inactive"] == -10.0

    def test_flat_space_is_one_region_with_every_parameter(self, get_experiment):
        # test_case_13 is flat, but its parameters sit under categories of N0 and are never active together
        _, search_space = get_experiment(13)

        regions = search_space.describe_regions()

        assert len(regions) == 1
        assert regions[0]["ActivationCategory"] == "root"
        assert {parameter["Name"] for parameter in regions[0]["Parameters"]} == {
            "Context.SearchSpace.N0",
            "Context.SearchSpace.N0.N01.F1",
            "Context.SearchSpace.N0.N01.N1",
            "Context.SearchSpace.N0.N02.I1",
            "Context.SearchSpace.N0.N02.O1",
        }
        types = {parameter["Name"]: parameter["Type"] for parameter in regions[0]["Parameters"]}
        assert types["Context.SearchSpace.N0.N02.I1"] == "IntegerHyperparameter"
        assert types["Context.SearchSpace.N0.N02.O1"] == "OrdinalHyperparameter"

    def test_description_is_json_serializable(self, get_experiment):
        for test_case in (13, 15, 16):
            _, search_space = get_experiment(test_case)

            assert json.loads(json.dumps(search_space.describe_regions())) == search_space.describe_regions()


class TestRegionActivation:
    """
    A region is active when its parent was chosen with exactly the region's activation category. The search space
    below has sibling categories whose names extend each other (A and AB), so a substring match of the category in
    the chosen values activates both branches when AB is chosen.
    """

    PARENT = "Context.SearchSpace.N0"
    CATEGORY_A = "Context.SearchSpace.N0.A"
    CATEGORY_AB = "Context.SearchSpace.N0.AB"
    CHILD_OF_A = "Context.SearchSpace.N0.A.F1"
    CHILD_OF_AB = "Context.SearchSpace.N0.AB.F2"

    @staticmethod
    def _search_space(structure: str) -> SearchSpace:
        def child(lower, upper, default):
            return {"Lower": lower, "Upper": upper, "Default": default, "Type": "FloatHyperparameter", "Level": 1}

        return SearchSpace({
            "N0": {
                "A": {"F1": child(0.0, 1.0, 0.5), "Type": "Category"},
                "AB": {"F2": child(0.0, 2.0, 1.0), "Type": "Category"},
                "Categories": [TestRegionActivation.CATEGORY_A, TestRegionActivation.CATEGORY_AB],
                "Default": TestRegionActivation.CATEGORY_A,
                "Type": "NominalHyperparameter",
                "Level": 0
            },
            "Structure": {structure: {}}
        })

    @staticmethod
    def _activated_categories(search_space: SearchSpace, chosen: dict) -> set:
        search_space.next_level()  # from the region of N0 to the regions of its categories
        try:
            activated = search_space.activate_regions(pd.DataFrame([chosen]))
        finally:
            search_space.reset_level()
        return {region[0].activation_category for region in activated}

    def test_category_whose_name_extends_a_sibling_activates_only_its_own_region(self):
        search_space = self._search_space("Hierarchical")

        assert self._activated_categories(search_space, {self.PARENT: self.CATEGORY_AB}) == {self.CATEGORY_AB}

    def test_category_that_is_the_start_of_a_sibling_activates_only_its_own_region(self):
        search_space = self._search_space("Hierarchical")

        assert self._activated_categories(search_space, {self.PARENT: self.CATEGORY_A}) == {self.CATEGORY_A}

    def test_no_region_is_activated_while_its_parent_is_missing(self):
        search_space = self._search_space("Hierarchical")

        assert self._activated_categories(search_space, {self.CHILD_OF_A: 0.5}) == set()

    def test_value_of_another_parameter_does_not_activate_a_region(self):
        # the string of a category inside the value of another parameter is not a choice of the parent
        search_space = self._search_space("Hierarchical")

        chosen = {self.PARENT: self.CATEGORY_A, "unrelated": self.CATEGORY_AB}

        assert self._activated_categories(search_space, chosen) == {self.CATEGORY_A}

    def test_flat_configuration_keeps_only_the_parameters_of_the_chosen_category(self):
        search_space = self._search_space("Flat")

        reduced = search_space.transform_flat_parameters_to_hierarchic(
            {self.PARENT: self.CATEGORY_AB, self.CHILD_OF_A: 0.5, self.CHILD_OF_AB: 1.5}
        )

        assert reduced == {self.PARENT: self.CATEGORY_AB, self.CHILD_OF_AB: 1.5}
