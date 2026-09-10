from analyzer.comparison.baseline_manager import BaselineResult
from analyzer.config import BenchmarkConfig
from analyzer.orchestration.comparative_orchestrator import ComparativeAnalysisOrchestrator
from tests.helpers.fakes import create_fake_experiment


def _build_config() -> BenchmarkConfig:
    return BenchmarkConfig.from_json(
        {
            "Benchmark": {
                "Report": {"outputDirectory": "./results/reports/"},
                "Resources": {"Folder": "./results/serialized/"},
                "Experiment": {"name": "cmp", "description": "cmp", "objectivesToMeasure": ["Y1"]},
                "Table": {},
                "ComparativeAnalysis": {
                    "RegretAnalysis": {
                        "knownOptimum": 9.0,
                        "optimumPerObjective": {"Y1": 1.0},
                        "regretType": ["iteration"],
                    },
                    "ComparativeTable": {},
                },
            }
        }
    )


def test_select_matching_baselines_prefers_task_match_over_fallback():
    orchestrator = ComparativeAnalysisOrchestrator(_build_config())

    exp = create_fake_experiment(
        "exp_task_x_model_s_sampler_cfg_sc_test_case_0",
        values=[{"Y1": 5.0}],
        description={"TaskConfiguration": {"TaskName": "Task-X"}},
    )

    matching_baseline_exp = create_fake_experiment(
        "exp_other_name",
        values=[{"Y1": 6.0}],
        description={"TaskConfiguration": {"TaskName": "Task-X"}},
    )
    non_matching_baseline_exp = create_fake_experiment(
        "exp_diff",
        values=[{"Y1": 7.0}],
        description={"TaskConfiguration": {"TaskName": "Task-Y"}},
    )

    baselines = {
        "b1": BaselineResult("b1", "baseline-one", [6.0], 6.0, matching_baseline_exp),
        "b2": BaselineResult("b2", "baseline-two", [7.0], 7.0, non_matching_baseline_exp),
    }

    matched = orchestrator._select_matching_baselines(exp, exp.name, baselines)

    assert [key for key, _ in matched] == ["b1"]


def test_compute_comparative_metrics_uses_per_objective_optimum_precedence(monkeypatch):
    orchestrator = ComparativeAnalysisOrchestrator(_build_config())

    exp = create_fake_experiment("exp_case", values=[{"Y1": 5.0}, {"Y1": 4.0}])
    baseline = BaselineResult("b1", "exp_case", [8.0, 6.0], 6.0, create_fake_experiment("exp_case", [{"Y1": 8.0}]))

    captured_known_optima = []

    def _fake_process(experiment_data, baseline, objective, known_optimum, **kwargs):
        captured_known_optima.append(known_optimum)
        return type("DummyResult", (), {"experiment_trajectory": [1.0], "baseline_trajectory": [1.0]})()

    monkeypatch.setattr(orchestrator.comparison_processor, "process_experiment_comparison", _fake_process)

    results = orchestrator.compute_comparative_metrics([exp], {"b1": baseline})

    assert "Y1" in results
    assert captured_known_optima == [1.0]
