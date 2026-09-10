from analyzer.comparison.comparison_processor import ComparisonResult
from analyzer.config import BenchmarkConfig
from analyzer.orchestration.benchmark_analyzer import BenchmarkAnalyzer


def _config_with_performance_profile() -> BenchmarkConfig:
    return BenchmarkConfig.from_json(
        {
            "Benchmark": {
                "Report": {"outputDirectory": "./results/reports/"},
                "Resources": {"Folder": "./results/serialized/"},
                "Experiment": {
                    "name": "profile",
                    "description": "profile",
                    "objectivesToMeasure": ["Y1", "Y2"],
                },
                "Table": {},
                "ComparativeAnalysis": {
                    "PerformanceProfile": {
                        "tauMax": 4.0,
                        "tauSteps": 20,
                        "objectivesToProfile": ["Y1", "Y2"],
                    },
                    "ComparativeTable": {},
                },
            }
        }
    )


def _result(exp_name: str, display_name: str, baseline_type: str, objective: str, traj):
    return ComparisonResult(
        experiment_name=exp_name,
        display_name=display_name,
        baseline_type=baseline_type,
        objective=objective,
        experiment_trajectory=traj,
        baseline_trajectory=None,
    )


def test_generate_global_performance_profile_returns_figure_for_complete_matrix():
    analyzer = BenchmarkAnalyzer(_config_with_performance_profile())

    comparative_results = {
        "Y1": [
            _result("exp_a", "test_case_0", "", "Y1", [5.0, 4.0]),
            _result("exp_b", "test_case_2", "", "Y1", [3.0, 2.0]),
        ],
        "Y2": [
            _result("exp_a", "test_case_0", "", "Y2", [8.0, 6.0]),
            _result("exp_b", "test_case_2", "", "Y2", [9.0, 7.0]),
        ],
    }

    fig = analyzer._generate_global_performance_profile(comparative_results)

    assert fig is not None
    assert len(fig.data) >= 2


def test_generate_global_performance_profile_returns_none_when_only_one_complete_test_case():
    analyzer = BenchmarkAnalyzer(_config_with_performance_profile())

    comparative_results = {
        "Y1": [
            _result("exp_a", "test_case_0", "", "Y1", [5.0, 4.0]),
            _result("exp_b", "test_case_2", "", "Y1", [3.0, 2.0]),
        ],
        "Y2": [
            _result("exp_a", "test_case_0", "", "Y2", [8.0, 6.0]),
        ],
    }

    fig = analyzer._generate_global_performance_profile(comparative_results)

    assert fig is None

