import numpy as np

from analyzer.comparison.comparative_metrics import (
    RelativeImprovementCalculator,
    PerformanceProfileCalculator,
    RegretCalculator,
)


def test_regret_calculator_supports_minimize_and_maximize_modes():
    assert RegretCalculator.calculate_regret_curve([5.0, 3.0, 4.0], known_optimum=1.0, minimize=True) == [4.0, 2.0, 2.0]
    assert RegretCalculator.calculate_regret_curve([2.0, 4.0, 3.0], known_optimum=10.0, minimize=False) == [8.0, 6.0, 6.0]


def test_regret_curve_time_requires_same_lengths():
    timed = RegretCalculator.calculate_regret_curve_time([3.0, 2.0], [0.0], known_optimum=0.0, minimize=True)
    assert timed == []


def test_relative_improvement_handles_zero_denominator_edge_cases():
    calc = RelativeImprovementCalculator()

    assert calc.calculate_relative_improvement(10.0, 10.0, minimize=True) == 1.0
    assert calc.calculate_relative_improvement(8.0, 10.0, minimize=True) == 1.25
    assert calc.calculate_relative_improvement(12.0, 10.0, minimize=True) == 10.0 / 12.0


def test_time_and_iteration_relative_improvement_are_clipped_and_guarded():
    calc = RelativeImprovementCalculator()

    assert calc.calculate_time_relative_improvement(experiment_time=5.0, baseline_time=100.0) == 10.0
    assert calc.calculate_time_relative_improvement(experiment_time=0.0, baseline_time=10.0) is None
    assert calc.calculate_iteration_relative_improvement([3.0, 2.0], [4.0, 3.0, 2.0], minimize=True) == 1.5


def test_performance_profile_calculator_builds_monotonic_profiles():
    ratios = PerformanceProfileCalculator.calculate_performance_ratios(
        {
            "algo_a": [1.0, 4.0, 2.0],
            "algo_b": [2.0, 2.0, 2.0],
        },
        minimize=True,
    )

    assert list(ratios.columns) == ["algo_a", "algo_b"]
    assert np.all(ratios.min(axis=1).values == 1.0)

    profile = PerformanceProfileCalculator.generate_performance_profile(ratios, tau_range=(1.0, 2.0), tau_steps=5)
    tau, rho = profile["algo_a"]

    assert len(tau) == 5
    assert len(rho) == 5
    assert np.all(np.diff(rho) >= -1e-12)
    assert 0.0 <= rho[0] <= rho[-1] <= 1.0