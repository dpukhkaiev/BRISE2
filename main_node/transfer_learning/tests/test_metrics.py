import pytest

from transfer_learning.model_recommendation.metrics.average_relative_improvement import \
    AverageRelativeImprovementMetric


def _prediction_info(models_per_region: dict) -> dict:
    return {region: {"Model": model, "time_to_build": 1} for region, model in models_per_region.items()}


class TestAverageRelativeImprovement:

    def test_samples_of_siblings_share_a_combination(self):
        prediction_infos = [
            _prediction_info({"0": ["A"], "1": ["B"]}),
            _prediction_info({"0": ["A"], "2": ["B"]}),
            _prediction_info({"0": ["A"], "1": ["D"]}),
        ]
        improvement_curve = [10.0, 9.9, 2.0, 1.9]

        metric = AverageRelativeImprovementMetric(is_minimization_experiment=True)
        result = metric.compute(improvement_curve, prediction_infos, 0, 3, multi_model=True)

        assert result["Model_combination"] == prediction_infos[0]
        # the first combination is held over two samples: (10.0 - 2.0) / 10.0 spread over both of them
        assert result["average_relative_improvement"] == 0.4

    def test_repeated_identical_combination_is_counted_once(self):
        prediction_infos = [
            _prediction_info({"0": ["A"], "1": ["B"]}),
            _prediction_info({"0": ["A"], "1": ["B"]}),
            _prediction_info({"0": ["A"], "1": ["D"]}),
        ]
        improvement_curve = [10.0, 9.9, 2.0, 1.9]

        metric = AverageRelativeImprovementMetric(is_minimization_experiment=True)
        result = metric.compute(improvement_curve, prediction_infos, 0, 3, multi_model=True)

        assert result["Model_combination"] == prediction_infos[0]
        assert result["average_relative_improvement"] == 0.4

    def test_a_deeper_branch_adds_a_model_type_to_the_combination(self):
        """
        A sample descending one level further is predicted with an additional model type,
        which does make it a combination of its own.
        """
        prediction_infos = [
            _prediction_info({"0": ["A"], "1": ["B"]}),
            _prediction_info({"0": ["A"], "1": ["B"], "3": ["C"]}),
        ]
        improvement_curve = [10.0, 9.0, 2.0]

        metric = AverageRelativeImprovementMetric(is_minimization_experiment=True)
        result = metric.compute(improvement_curve, prediction_infos, 0, 2, multi_model=True)

        assert result["Model_combination"] == prediction_infos[1]


class TestImprovementByDirection:
    """The improvement is the progress of the best result towards the better direction, relative to the value it started from."""

    @staticmethod
    def _improvement(curve: list, minimization: bool, models: list, multi_model: bool) -> dict:
        # each model predicts one sample, and the curve starts with the best result before the first of them;
        # the interval runs from its start to its last value
        prediction_infos = [_prediction_info({"0": [model]}) for model in models]
        metric = AverageRelativeImprovementMetric(is_minimization_experiment=minimization)
        return metric.compute(curve, prediction_infos, 0, len(curve) - 1, multi_model=multi_model)

    def test_a_falling_minimized_result_is_an_improvement_over_one_sample(self):
        result = self._improvement([10.0, 5.0], minimization=True, models=["A"], multi_model=False)

        assert result["average_relative_improvement"] == 0.5

    def test_a_rising_maximized_result_is_an_improvement_over_one_sample(self):
        result = self._improvement([10.0, 15.0], minimization=False, models=["A"], multi_model=False)

        assert result["average_relative_improvement"] == 0.5

    def test_a_falling_negative_minimized_result_is_an_improvement_over_one_sample(self):
        result = self._improvement([-5.0, -10.0], minimization=True, models=["A"], multi_model=False)

        assert result["average_relative_improvement"] == 1.0

    def test_a_maximized_result_rising_across_zero_is_an_improvement_over_one_sample(self):
        # -5 -> 5 is progress of 10, relative to the 5 it started from
        result = self._improvement([-5.0, 5.0], minimization=False, models=["A"], multi_model=False)

        assert result["average_relative_improvement"] == 2.0

    def test_a_rising_maximized_result_of_a_combination_followed_by_another_is_relative_to_its_start(self):
        # A holds the sample for one step, 10 -> 15: 0.5 of its start. B holds it for the next, 15 -> 20: a third of its start
        result = self._improvement([10.0, 15.0, 20.0], minimization=False, models=["A", "B"], multi_model=True)

        assert result["Model_combination"] == _prediction_info({"0": ["A"]})
        assert result["average_relative_improvement"] == 0.5

    def test_a_falling_negative_minimized_result_of_a_combination_followed_by_another_is_an_improvement(self):
        # A: -5 -> -10, 1.0 of its start; B: -10 -> -11, a tenth of its start
        result = self._improvement([-5.0, -10.0, -11.0], minimization=True, models=["A", "B"], multi_model=True)

        assert result["Model_combination"] == _prediction_info({"0": ["A"]})
        assert result["average_relative_improvement"] == 1.0

    def test_a_rising_maximized_result_of_a_combination_held_to_the_end_is_relative_to_its_start(self):
        # A holds the samples for both steps, 10 -> 20: 1.0 of its start, spread over the 2 steps
        result = self._improvement([10.0, 15.0, 20.0], minimization=False, models=["A", "A"], multi_model=True)

        assert result["average_relative_improvement"] == 0.5

    def test_a_falling_negative_minimized_result_of_a_combination_held_to_the_end_is_an_improvement(self):
        # A: -5 -> -6, a fifth of its start; B, held to the end: -6 -> -10, two thirds of its start
        result = self._improvement([-5.0, -6.0, -10.0], minimization=True, models=["A", "B"], multi_model=True)

        assert result["Model_combination"] == _prediction_info({"0": ["B"]})
        assert result["average_relative_improvement"] == pytest.approx(2 / 3)
