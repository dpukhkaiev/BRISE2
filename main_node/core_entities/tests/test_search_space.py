import numpy as np
import pandas as pd

from core_entities.search_space import FloatHyperparameter, IntegerHyperparameter, NominalHyperparameter


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
