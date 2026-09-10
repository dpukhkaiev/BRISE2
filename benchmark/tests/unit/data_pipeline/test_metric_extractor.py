import math
from datetime import datetime

import numpy as np
import pandas as pd

from analyzer.config import MetricType
from analyzer.data_pipeline.metric_extractor import MetricExtractor
from analyzer.visualization.plot_generator import PlotGenerator
from tests.helpers.fakes import create_fake_experiment


def test_extract_objective_series_tracks_best_so_far_with_enabled_guard():
    exp = create_fake_experiment(
        "exp_case",
        values=[{"Y1": 5.0}, {"Y1": 3.0}, {"Y1": 4.0}, {"Y1": 2.0}],
        is_enabled=[True, False, True, True],
    )

    series = MetricExtractor.extract_objective_series(exp, "Y1")

    assert series == [5.0, 5.0, 4.0, 2.0]


def test_extract_grouped_data_time_metric_computes_statistics_and_mean_time_axis():
    start = datetime(2024, 1, 1, 0, 0, 0)
    exp_a = create_fake_experiment("exp_a", values=[{"Y1": 6.0}, {"Y1": 4.0}], start_time=start)
    exp_b = create_fake_experiment("exp_b", values=[{"Y1": 5.0}], start_time=start)

    grouped = MetricExtractor.extract_grouped_data([exp_a, exp_b], "Y1", metric_type=MetricType.TIME.value)

    # Past the end of exp_b we aggregate over exp_a only (no forward-fill).
    assert grouped["mean_values"] == [5.5, 4.0]
    assert grouped["min_values"] == [5.0, 4.0]
    assert grouped["max_values"] == [6.0, 4.0]
    assert grouped["sample_counts"] == [2, 1]
    assert grouped["metric_values"] == [0.0, 10.0]


def test_prepare_grouped_plot_data_drops_indices_below_min_reps():
    grouped = {
        "metric_values": [0, 1, 2, 3],
        "mean_values": [10.0, 9.0, 8.0, 7.0],
        "std_values": [0.5, 0.4, 0.3, 0.2],
        "sample_counts": [5, 3, 1, 0],
    }

    x, mean_y, _, _ = PlotGenerator._prepare_grouped_plot_data(grouped, min_reps=3)

    # idx 2 (1 sample) and idx 3 (0 samples) are dropped; idx 0 and 1 remain.
    assert x == [0, 1]
    assert mean_y == [10.0, 9.0]


def test_prepare_grouped_plot_data_default_threshold_keeps_single_sample_tail():
    grouped = {
        "metric_values": [0, 1],
        "mean_values": [5.0, 4.0],
        "std_values": [0.0, 0.0],
        "sample_counts": [3, 1],
    }

    x, _, _, _ = PlotGenerator._prepare_grouped_plot_data(grouped)

    # Default min_reps=1 matches the legacy "show any sample" behavior.
    assert x == [0, 1]


def _seaborn_equivalent_stats(series_list):
    """Reference aggregation matching seaborn lineplot(ci='sd') on a long-format frame.

    The legacy notebook ``analyse_flat_search_space.ipynb`` builds a long DataFrame
    with one row per (repetition, iteration) and lets seaborn aggregate. That is
    exactly groupby('iteration').agg(mean, std) using the population std (ddof=0),
    which is what numpy's nanstd uses and what the extractor produces.
    """
    rows = [
        {"iteration": i, "objective": v}
        for s in series_list
        for i, v in enumerate(s)
    ]
    df = pd.DataFrame(rows)
    grouped = df.groupby("iteration")["objective"]
    return grouped.mean().tolist(), grouped.std(ddof=0).tolist(), grouped.count().tolist()


def test_grouped_aggregation_matches_seaborn_long_format_groupby():
    # Ragged repetitions: 3 reps with different lengths simulate the notebook's
    # repetitions reaching different last iterations.
    series = [
        [10.0, 9.0, 8.0, 7.0, 7.0],   # 5 iterations
        [10.0, 8.5, 8.5],             # 3 iterations
        [10.0, 9.5, 8.0, 7.5],        # 4 iterations
    ]
    expected_mean, expected_std, expected_count = _seaborn_equivalent_stats(series)

    grouped = MetricExtractor.extract_grouped_series_data(series, metric_type=MetricType.ITERATION.value)

    np.testing.assert_allclose(grouped["mean_values"], expected_mean)
    np.testing.assert_allclose(grouped["std_values"], expected_std)
    assert grouped["sample_counts"] == expected_count


def test_min_reps_equal_to_group_size_reproduces_truncate_to_shortest_rep():
    # Setting min_reps to the number of repetitions reproduces the strictest
    # "all reps must contribute" view (i.e., truncate to the shortest rep).
    series = [
        [10.0, 9.0, 8.0, 7.0, 7.0],
        [10.0, 8.5, 8.5],
        [10.0, 9.5, 8.0, 7.5],
    ]
    grouped = MetricExtractor.extract_grouped_series_data(series)

    x_vals, mean_y, _, _ = PlotGenerator._prepare_grouped_plot_data(grouped, min_reps=len(series))

    # Only iterations 0, 1, 2 have data from all 3 reps; 3 and 4 are dropped.
    assert x_vals == [0, 1, 2]
    np.testing.assert_allclose(mean_y, [10.0, 9.0, 8.166666666666666])


def test_prepare_grouped_plot_data_ratio_threshold_filters_sparse_tail():
    # 10 reps total; 8 have data at all 3 indices, only 2 survive past index 2.
    # With min_reps_ratio=0.5, threshold = round(10 * 0.5) = 5.
    # Index 2 has only 2 samples < 5 → dropped.
    grouped = {
        "metric_values": [0, 1, 2],
        "mean_values": [10.0, 9.0, 8.0],
        "std_values": [0.5, 0.4, 0.3],
        "sample_counts": [10, 8, 2],
    }

    x, mean_y, _, _ = PlotGenerator._prepare_grouped_plot_data(grouped, min_reps_ratio=0.5)

    assert x == [0, 1]
    assert mean_y == [10.0, 9.0]


def test_prepare_grouped_plot_data_ratio_overrides_absolute_min_reps():
    # min_reps=1 would keep everything; ratio=0.5 → threshold=5 must take precedence.
    grouped = {
        "metric_values": [0, 1, 2],
        "mean_values": [10.0, 9.0, 8.0],
        "std_values": [0.5, 0.4, 0.3],
        "sample_counts": [10, 6, 2],
    }

    x, _, _, _ = PlotGenerator._prepare_grouped_plot_data(grouped, min_reps=1, min_reps_ratio=0.5)

    # threshold = round(10 * 0.5) = 5; index 2 (count=2) is dropped
    assert x == [0, 1]


def test_discover_objectives_filters_non_numeric_and_nan_values():
    exp = create_fake_experiment(
        "exp_case",
        values=[
            {"Y1": 1.0, "tag": "n/a", "bad": math.nan},
            {"Y2": 2, "text": "x"},
            {"Y3": 3.5},
            {"Y4": 4.5},
        ],
    )

    objectives = MetricExtractor.discover_objectives([exp])
    assert objectives == {"Y1", "Y2", "Y3", "Y4"}


