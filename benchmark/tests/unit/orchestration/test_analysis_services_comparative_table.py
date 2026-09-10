from analyzer.comparison.comparison_processor import ComparisonResult
from analyzer.config.benchmark_config import ComparativeTableConfig
from analyzer.orchestration.analysis_services import ComparativeTableService


def test_comparative_table_service_respects_column_toggles_and_direction():
    result = ComparisonResult(
        experiment_name="exp_case",
        display_name="test_case_0",
        baseline_type="baseline_grid-search",
        objective="Y1",
        relative_improvement=0.25,
        relative_improvement_time=2.5,
        relative_improvement_iterations=1.5,
        converged_at_iteration=4,
        experiment_trajectory=[1.0, 3.0, 2.0],
        baseline_trajectory=[0.5, 1.5, 2.5],
        final_regret=0.01,
    )

    cfg = ComparativeTableConfig(
        experiment=True,
        baseline=False,
        relative_improvement=True,
        speedup_factor=True,
        converged_at_iteration=True,
        experiment_best=True,
        baseline_best=True,
        final_regret=True,
    )

    table = ComparativeTableService.build(
        {"Y1": [result]},
        table_config=cfg,
        is_minimizing_fn=lambda _objective: False,
    )

    row = table["Y1"][0]
    assert "Baseline" not in row
    assert row["Experiment"] == "test_case_0"
    assert row["RI (Objective)"] == "0.2500"
    assert row["RI (Time)"] == "2.5000"
    assert row["RI (Iterations)"] == "1.5000"
    assert row["Converged at Iter"] == 4
    assert row["Experiment Best"] == "3.000000"
    assert row["Baseline Best"] == "2.500000"
    assert row["Final Regret"] == "0.010000"

