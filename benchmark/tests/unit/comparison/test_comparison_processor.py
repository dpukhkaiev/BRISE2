from datetime import datetime, timedelta

from analyzer.comparison.baseline_manager import BaselineResult
from analyzer.comparison.comparison_processor import ComparisonProcessor
from analyzer.config import BenchmarkConfig


def _build_comparison_config() -> BenchmarkConfig:
    return BenchmarkConfig.from_json(
        {
            "Benchmark": {
                "Report": {"outputDirectory": "./results/reports/"},
                "Resources": {"Folder": "./results/serialized/"},
                "Experiment": {"name": "cmp", "description": "cmp", "objectivesToMeasure": ["Y1"]},
                "Table": {},
                "ComparativeAnalysis": {
                    "RegretAnalysis": {"knownOptimum": 0.0, "regretType": ["iteration", "time"]},
                    "RelativeImprovement": {
                        "improvementType": ["objective_value", "time_to_target", "iteration_to_target"]
                    },
                    "ComparativeTable": {},
                },
            }
        }
    )


def test_process_experiment_comparison_computes_all_requested_metrics():
    cfg = _build_comparison_config()
    processor = ComparisonProcessor(cfg)

    raw_baseline = type("RawBaseline", (), {})()
    raw_baseline.start_time = datetime(2024, 1, 1, 10, 0, 0)
    raw_baseline.end_time = raw_baseline.start_time + timedelta(seconds=60)

    baseline = BaselineResult(
        baseline_id="baseline_1",
        baseline_type="grid-search",
        trajectory=[12.0, 8.0, 6.0],
        best_value=6.0,
        raw_experiment=raw_baseline,
    )

    experiment_data = {
        "name": "exp_test_case_0",
        "display_name": "test_case_0",
        "trajectory": {"Y1": [9.0, 7.0, 5.0]},
        "runtime": 30.0,
        "timestamps": [0.0, 10.0, 20.0],
    }

    result = processor.process_experiment_comparison(
        experiment_data=experiment_data,
        baseline=baseline,
        objective="Y1",
        known_optimum=0.0,
    )

    assert result.regret_curve == [9.0, 7.0, 5.0]
    assert result.regret_curve_time == [(0.0, 9.0), (10.0, 7.0), (20.0, 5.0)]
    assert result.final_regret == 5.0
    assert result.relative_improvement == 6.0 / 5.0
    assert result.relative_improvement_time == 2.0
    assert result.relative_improvement_iterations == 1.0
    assert result.converged_at_iteration == 3


def test_process_experiment_comparison_respects_maximization_direction():
    cfg = _build_comparison_config()
    cfg.optimization_direction = {"Y1": "maximize"}
    processor = ComparisonProcessor(cfg)

    baseline = BaselineResult(
        baseline_id="baseline_1",
        baseline_type="random-search",
        trajectory=[3.0, 4.0, 5.0],
        best_value=5.0,
        raw_experiment=None,
    )

    experiment_data = {
        "name": "exp_max_case",
        "trajectory": {"Y1": [1.0, 3.0, 2.0]},
        "runtime": 15.0,
    }

    result = processor.process_experiment_comparison(
        experiment_data=experiment_data,
        baseline=baseline,
        objective="Y1",
        known_optimum=10.0,
    )

    assert result.regret_curve == [9.0, 7.0, 7.0]
    assert result.converged_at_iteration == 2