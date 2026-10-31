from types import SimpleNamespace

import pandas as pd

from configuration_selection.model.predictor import Predictor
from core_entities.configuration import Configuration, PartialConfiguration


def _make_config(parameters):
    return Configuration(parameters, Configuration.Type.TEST, "experiment_id")


def _make_region(parent_name, activation_category, hp_names):
    parent = SimpleNamespace(name=parent_name)
    return tuple(SimpleNamespace(parent=parent, activation_category=activation_category, name=hp_name)
                 for hp_name in hp_names)


class TestRegionPredictionsAreMerged:

    def test_parameters_of_every_region_are_kept_and_objectives_do_not_collide(self):
        """
        Each hierarchical region's model predicts the same objective names, so a point walking several
        regions must keep every region's parameters and still end up with one value per objective.
        """
        region_names = [f"hp{i}" for i in range(4)]
        point = PartialConfiguration()
        for i, hp_name in enumerate(region_names):
            point.absorb(pd.Series({hp_name: i, "Y1": float(i)}), _make_region("root", "root", [hp_name]))

        configuration = point.to_configuration("experiment_id", prediction_info={})
        assert configuration.parameters == {hp_name: i for i, hp_name in enumerate(region_names)}
        assert configuration.predicted_result == [1.5]

    def test_single_region_prediction_is_returned_as_is(self):
        point = PartialConfiguration()
        point.absorb(pd.Series({"hp0": 1, "Y1": 0.5}), _make_region("root", "root", ["hp0"]))

        configuration = point.to_configuration("experiment_id", prediction_info={})
        assert configuration.parameters == {"hp0": 1}
        assert configuration.predicted_result == [0.5]


class TestConsideredConfigsForRegion:

    def test_sibling_regions_are_scoped_independently(self):
        """
        Two sibling regions (same parent, different activation categories) must each be scoped from the
        full base window, not from whatever the other sibling's filtering left behind.
        """
        base_considered_configs = [
            _make_config({"algorithm": "A", "A.param": 1}),
            _make_config({"algorithm": "B", "B.param": 2}),
        ]
        region_a = _make_region("algorithm", "A", ["A.param"])
        region_b = _make_region("algorithm", "B", ["B.param"])

        configs_for_a = Predictor._configs_within_region(region_a, base_considered_configs)
        configs_for_b = Predictor._configs_within_region(region_b, base_considered_configs)

        assert [c.parameters["algorithm"] for c in configs_for_a] == ["A"]
        assert [c.parameters["algorithm"] for c in configs_for_b] == ["B"]

    def test_root_level_region_skips_activation_category_filter(self):
        base_considered_configs = [_make_config({"algorithm": "A"})]
        root_region = _make_region("root", "root", ["algorithm"])

        configs = Predictor._configs_within_region(root_region, base_considered_configs)

        assert configs == base_considered_configs

    def test_configs_from_an_unrelated_branch_lacking_the_parent_key_are_excluded_not_erroring(self):
        """
        A deeper region's parent hyperparameter (e.g. under branch N01) is absent from configs
        measured along a different branch: those configs must be filtered out.
        """
        base_considered_configs = [
            _make_config({"branch": "N01", "N01.O1": "N01.O1.X", "N01.O1.X.param": 1}),
            _make_config({"branch": "N02", "N02.param": 2}),
        ]
        deeper_region = _make_region("N01.O1", "N01.O1.X", ["N01.O1.X.param"])

        configs = Predictor._configs_within_region(deeper_region, base_considered_configs)

        assert [c.parameters["branch"] for c in configs] == ["N01"]

    def test_base_considered_configs_is_not_mutated(self):
        base_considered_configs = [
            _make_config({"algorithm": "A", "A.param": 1}),
            _make_config({"algorithm": "B", "B.param": 2}),
        ]
        original = list(base_considered_configs)
        region_a = _make_region("algorithm", "A", ["A.param"])

        Predictor._configs_within_region(region_a, base_considered_configs)

        assert base_considered_configs == original


class TestAveragePredictionsPerObjective:

    @staticmethod
    def _predicted_result(*rows):
        point = PartialConfiguration()
        for i, row in enumerate(rows):
            hp_name = f"hp{i}"
            point.absorb(pd.Series({hp_name: i, **row}), _make_region("root", "root", [hp_name]))
        return point.to_configuration("experiment_id", prediction_info={}).predicted_result

    def test_predictions_of_one_objective_from_several_regions_are_averaged(self):
        assert self._predicted_result({"Y1": 1.0}, {"Y1": 2.0}, {"Y1": 6.0}) == [3.0]

    def test_every_objective_keeps_its_own_average(self):
        assert self._predicted_result({"Y1": 1.0, "Y2": 10.0}, {"Y1": 3.0, "Y2": 20.0}) == [2.0, 15.0]
