from types import SimpleNamespace

import pandas as pd

from configuration_selection.model.predictor import Predictor
from core_entities.configuration import Configuration


def _make_config(parameters):
    return Configuration(parameters, Configuration.Type.TEST, "experiment_id")


def _make_region(parent_name, activation_category, hp_names):
    parent = SimpleNamespace(name=parent_name)
    return tuple(SimpleNamespace(parent=parent, activation_category=activation_category, name=hp_name)
                 for hp_name in hp_names)


class TestUpdatePrediction:

    def test_updating_prediction_with_colliding_objective_columns(self):
        """
        Each hierarchical region's model predicts the same objective column names, so merging several regions'
        predictions must rename those columns.
        """
        region_names = [f"hp{i}" for i in range(4)]
        predicted = pd.DataFrame()
        for i, hp_name in enumerate(region_names):
            partial_configuration = pd.DataFrame({hp_name: [i], "Y1": [float(i)]})
            predicted = Predictor._update_prediction(None, predicted, partial_configuration, str(i), [hp_name])

        assert len(predicted) == 1
        assert set(region_names).issubset(predicted.columns)

        objective_columns = [c for c in predicted.columns if c not in region_names]
        assert len(objective_columns) == len(region_names)
        assert len(set(objective_columns)) == len(objective_columns)
        assert sorted(predicted[objective_columns].iloc[0].tolist()) == [0.0, 1.0, 2.0, 3.0]

    def test_updating_prediction_with_no_prior_predictions_returns_partial_configuration_unchanged(self):
        partial_configuration = pd.DataFrame({"hp0": [1], "Y1": [0.5]})
        merged = Predictor._update_prediction(None, pd.DataFrame(), partial_configuration, "0", ["hp0"])

        pd.testing.assert_frame_equal(merged, partial_configuration)


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

        configs_for_a = Predictor._considered_configs_for_region(None, base_considered_configs, region_a, ["A.param"])
        configs_for_b = Predictor._considered_configs_for_region(None, base_considered_configs, region_b, ["B.param"])

        assert [c.parameters["algorithm"] for c in configs_for_a] == ["A"]
        assert [c.parameters["algorithm"] for c in configs_for_b] == ["B"]

    def test_root_level_region_skips_activation_category_filter(self):
        base_considered_configs = [_make_config({"algorithm": "A"})]
        root_region = _make_region("root", "root", ["algorithm"])

        configs = Predictor._considered_configs_for_region(None, base_considered_configs, root_region, ["algorithm"])

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

        configs = Predictor._considered_configs_for_region(None, base_considered_configs, deeper_region,
                                                            ["N01.O1.X.param"])

        assert [c.parameters["branch"] for c in configs] == ["N01"]

    def test_base_considered_configs_is_not_mutated(self):
        base_considered_configs = [
            _make_config({"algorithm": "A", "A.param": 1}),
            _make_config({"algorithm": "B", "B.param": 2}),
        ]
        original = list(base_considered_configs)
        region_a = _make_region("algorithm", "A", ["A.param"])

        Predictor._considered_configs_for_region(None, base_considered_configs, region_a, ["A.param"])

        assert base_considered_configs == original


class TestAveragePredictionsPerObjective:

    def test_predictions_of_one_objective_from_several_regions_are_averaged(self):
        predicted_values = pd.Series({"Y1": 1.0, "Y1__region2": 2.0, "Y1__region3": 6.0})
        averaged = Predictor._average_predictions_per_objective(None, predicted_values)

        assert averaged == {"Y1": 3.0}

    def test_every_objective_keeps_its_own_average(self):
        predicted_values = pd.Series(
            {"Y1": 1.0, "Y2": 10.0, "Y1__region2": 3.0, "Y2__region2": 20.0}
        )
        averaged = Predictor._average_predictions_per_objective(None, predicted_values)

        assert averaged == {"Y1": 2.0, "Y2": 15.0}
        assert list(averaged.keys()) == ["Y1", "Y2"]

    def test_single_region_prediction_is_returned_as_is(self):
        predicted_values = pd.Series({"Y1": 0.5})
        averaged = Predictor._average_predictions_per_objective(None, predicted_values)

        assert averaged == {"Y1": 0.5}
