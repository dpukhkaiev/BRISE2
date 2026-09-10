from analyzer.comparison.baseline_manager import BaselineResult
from analyzer.config import BenchmarkConfig, NormalizationType, TableConfig
from analyzer.data_pipeline import DataProcessor
from analyzer.orchestration.benchmark_analyzer import BenchmarkAnalyzer


def _make_config() -> BenchmarkConfig:
    return BenchmarkConfig(
        results_folder="./results/serialized/",
        output_directory="./results/reports/",
        experiment_name="test",
        experiment_description="test",
        objectives_to_measure=["Y1"],
        plots=[],
        table_config=TableConfig(),
    )


def test_normalize_with_baselines_min_over_all_uses_single_scale_for_all_series():
    analyzer = BenchmarkAnalyzer(_make_config())
    data_series = [[4.0, 2.0], [8.0]]
    baselines = {
        "base": BaselineResult(
            baseline_id="base",
            baseline_type="base",
            trajectory=[1.0, 3.0],
            best_value=1.0,
            raw_experiment=None,
        )
    }

    normalized_series, normalized_baselines = analyzer._normalize_with_baselines(
        data_series, baselines, "Y1", NormalizationType.MIN_OVER_ALL.value
    )

    assert normalized_series == [[4.0, 2.0], [8.0]]
    assert normalized_baselines["base"].trajectory == [1.0, 3.0]


def test_normalize_with_baselines_none_leaves_inputs_unchanged():
    analyzer = BenchmarkAnalyzer(_make_config())
    data_series = [[4.0, 2.0]]
    baselines = {
        "base": BaselineResult(
            baseline_id="base",
            baseline_type="base",
            trajectory=[2.0],
            best_value=2.0,
            raw_experiment=None,
        )
    }

    normalized_series, normalized_baselines = analyzer._normalize_with_baselines(
        data_series, baselines, "Y1", NormalizationType.NONE.value
    )

    assert normalized_series == data_series
    assert normalized_baselines is baselines

def test_data_processor_normalize_series_max_over_all():
    series = [[1.0, 2.0, None], [4.0, 0.0]]

    normalized = DataProcessor.normalize_series(series, NormalizationType.MAX_OVER_ALL.value)

    assert normalized == [[0.25, 0.5, None], [1.0, 0.0]]


def test_data_processor_normalize_series_max_over_all_zero_guard():
    series = [[0.0, 0.0], [0.0]]

    normalized = DataProcessor.normalize_series(series, NormalizationType.MAX_OVER_ALL.value)

    assert normalized == series


def test_normalize_with_baselines_max_over_all_uses_shared_global_max():
    analyzer = BenchmarkAnalyzer(_make_config())

    data_series = [[1.0, 2.0], [3.0, 4.0]]
    baselines = {
        "baseline_a": BaselineResult(
            baseline_id="baseline_a",
            baseline_type="baseline_a",
            trajectory=[8.0, 6.0],
            best_value=6.0,
            raw_experiment=None,
        )
    }

    normalized_series, normalized_baselines = analyzer._normalize_with_baselines(
        data_series,
        baselines,
        "Y1",
        NormalizationType.MAX_OVER_ALL.value,
    )

    assert normalized_series == [[0.125, 0.25], [0.375, 0.5]]
    assert normalized_baselines["baseline_a"].trajectory == [1.0, 0.75]
    assert normalized_baselines["baseline_a"].best_value == 1.0
