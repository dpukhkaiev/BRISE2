import pandas as pd

from configuration_selection.model.predictor import Predictor


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
