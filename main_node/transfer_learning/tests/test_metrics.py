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
