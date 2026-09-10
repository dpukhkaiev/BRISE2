from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd


class RegretCalculator:
    """Calculates regret metrics (distance to known optimum)"""

    @staticmethod
    def calculate_instant_regret(objective_value: float, known_optimum: float, minimize: bool = True) -> float:
        return objective_value - known_optimum if minimize else known_optimum - objective_value

    @staticmethod
    def calculate_regret_curve(objective_series: List[float], known_optimum: float, minimize: bool = True) -> List[float]:
        current_best = float('inf') if minimize else float('-inf')
        best_so_far = []
        for value in objective_series:
            current_best = min(current_best, value) if minimize else max(current_best, value)
            best_so_far.append(current_best)
        return [RegretCalculator.calculate_instant_regret(v, known_optimum, minimize) for v in best_so_far]

    @staticmethod
    def calculate_regret_curve_time(
        objective_series: List[float],
        timestamps: List[float],
        known_optimum: float,
        minimize: bool = True
    ) -> List[Tuple[float, float]]:
        if len(objective_series) != len(timestamps):
            return []
        regrets = RegretCalculator.calculate_regret_curve(objective_series, known_optimum, minimize)
        return list(zip(timestamps, regrets))

    @staticmethod
    def calculate_cumulative_regret(objective_series: List[float], known_optimum: float, minimize: bool = True) -> float:
        return sum(RegretCalculator.calculate_instant_regret(v, known_optimum, minimize) for v in objective_series)


class RelativeImprovementCalculator:
    """Calculates relative improvement vs baseline"""

    @staticmethod
    def calculate_relative_improvement(
        experiment_value: float,
        baseline_value: float,
        minimize: bool = True,
    ) -> Optional[float]:
        if experiment_value <= 0 or baseline_value <= 0:
            return None
        if minimize:
            return baseline_value / experiment_value
        return experiment_value / baseline_value

    @staticmethod
    def calculate_time_relative_improvement(experiment_time: float, baseline_time: float) -> Optional[float]:
        """Returns speedup ratio: baseline_time / experiment_time. >1 = faster than baseline."""
        if experiment_time <= 0:
            return None
        return max(0.0, min(10.0, baseline_time / experiment_time))

    @staticmethod
    def calculate_iteration_relative_improvement(
        experiment_trajectory: List[float],
        baseline_trajectory: List[float],
        minimize: bool = True
    ) -> Optional[float]:
        """Returns speedup ratio: baseline_iters / experiment_iters. >1 = more efficient."""
        if not experiment_trajectory or not baseline_trajectory or len(experiment_trajectory) == 0:
            return None
        return len(baseline_trajectory) / len(experiment_trajectory)


class PerformanceProfileCalculator:
    """Generates performance profiles for algorithm comparison"""

    @staticmethod
    def calculate_performance_ratios(algorithms: Dict[str, List[float]], minimize: bool = True) -> pd.DataFrame:
        df = pd.DataFrame(algorithms)
        best_values = df.min(axis=1) if minimize else df.max(axis=1)
        ratios = df.copy()
        for col in df.columns:
            ratios[col] = df[col] / best_values if minimize else best_values / df[col]
        return ratios

    @staticmethod
    def generate_performance_profile(
        performance_ratios: pd.DataFrame,
        tau_range: Optional[Tuple[float, float]] = None,
        tau_steps: int = 100
    ) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        """Generates performance profile curves: ρ(τ) = (1/n_problems) * |{p: ratio_p ≤ τ}|"""
        if tau_range is None:
            tau_range = (1.0, float(performance_ratios.max().max()))

        tau_values = np.linspace(tau_range[0], tau_range[1], tau_steps)
        n_problems = len(performance_ratios)

        return {
            algorithm: (tau_values, np.array([np.sum(performance_ratios[algorithm].values <= tau) / n_problems for tau in tau_values]))
            for algorithm in performance_ratios.columns
        }
