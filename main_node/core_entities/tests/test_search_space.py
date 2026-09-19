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
