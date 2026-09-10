from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
from dataclasses import dataclass

from analyzer.comparison.comparative_metrics import (
    RegretCalculator,
    RelativeImprovementCalculator,
    PerformanceProfileCalculator
)
from analyzer.comparison.baseline_manager import BaselineResult
from analyzer.config.benchmark_config import BenchmarkConfig, OptimizationDirection
from analyzer.util.trajectory_utils import extract_baseline_trajectory


@dataclass
class ComparisonResult:
    """Container for comparison results between experiment and baseline"""
    experiment_name: str
    display_name: Optional[str]
    baseline_type: str
    objective: str

    regret_curve: Optional[List[float]] = None
    regret_curve_time: Optional[List[Tuple[float, float]]] = None
    baseline_regret_curve: Optional[List[float]] = None
    baseline_regret_curve_time: Optional[List[Tuple[float, float]]] = None
    final_regret: Optional[float] = None
    cumulative_regret: Optional[float] = None

    relative_improvement: Optional[float] = None
    relative_improvement_time: Optional[float] = None
    relative_improvement_iterations: Optional[float] = None

    converged_at_iteration: Optional[int] = None

    experiment_trajectory: Optional[List[float]] = None
    baseline_trajectory: Optional[List[float]] = None
    known_optimum: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class ComparisonProcessor:
    """Computes comparative metrics between experiments and baselines"""

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.regret_calc = RegretCalculator()
        self.relative_calc = RelativeImprovementCalculator()
        self.profile_calc = PerformanceProfileCalculator()

    def process_experiment_comparison(
        self,
        experiment_data: Dict[str, Any],
        baseline: BaselineResult,
        objective: str,
        known_optimum: Optional[float] = None,
        result_key: Optional[str] = None,
    ) -> ComparisonResult:
        experiment_name = experiment_data.get('name', 'unknown')
        display_name = experiment_data.get('display_name', experiment_name)

        exp_trajectory = self._extract_trajectory(experiment_data, objective)
        minimize = self._is_minimizing(objective)
        baseline_trajectory = self._extract_baseline_trajectory(baseline, objective, minimize, result_key=result_key)

        self._warn_on_scale_mismatch(exp_trajectory, baseline_trajectory, experiment_name, baseline.baseline_type)

        result = ComparisonResult(
            experiment_name=experiment_name,
            display_name=display_name,
            baseline_type=baseline.baseline_type,
            objective=objective,
            experiment_trajectory=exp_trajectory,
            baseline_trajectory=baseline_trajectory,
            known_optimum=known_optimum
        )

        if known_optimum is not None and self.config.comparative_analysis.regret_analysis is not None:
            self._compute_regret(result, exp_trajectory, known_optimum, experiment_data, minimize, baseline)

        if self.config.comparative_analysis.relative_improvement is not None:
            self._compute_relative_improvement(result, exp_trajectory, baseline_trajectory, experiment_data, baseline, minimize)

        if exp_trajectory:
            result.converged_at_iteration = self._find_convergence_iteration(exp_trajectory, minimize)

        return result

    def _compute_regret(self, result: ComparisonResult, exp_trajectory: List[float], known_optimum: float,
                    experiment_data: Dict, minimize: bool, baseline: BaselineResult):
        regret_types = self.config.comparative_analysis.regret_analysis.regret_type

        if "iteration" in regret_types:
            result.regret_curve = self.regret_calc.calculate_regret_curve(exp_trajectory, known_optimum, minimize)
            result.final_regret = result.regret_curve[-1] if result.regret_curve else None
            result.cumulative_regret = self.regret_calc.calculate_cumulative_regret(exp_trajectory, known_optimum, minimize)
            if result.baseline_trajectory:
                result.baseline_regret_curve = self.regret_calc.calculate_regret_curve(
                    result.baseline_trajectory, known_optimum, minimize
                )

        if "time" in regret_types:
            timestamps = self._extract_timestamps(experiment_data, len(exp_trajectory))
            if timestamps:
                result.regret_curve_time = self.regret_calc.calculate_regret_curve_time(exp_trajectory, timestamps, known_optimum, minimize)
            if result.baseline_trajectory:
                baseline_timestamps = self._extract_baseline_timestamps(baseline, len(result.baseline_trajectory))
                if baseline_timestamps:
                    result.baseline_regret_curve_time = self.regret_calc.calculate_regret_curve_time(
                        result.baseline_trajectory, baseline_timestamps, known_optimum, minimize
                    )

    def _compute_relative_improvement(self, result: ComparisonResult, exp_trajectory: List[float], baseline_trajectory: List[float], experiment_data: Dict, baseline: BaselineResult, minimize: bool):
        improvement_types = self.config.comparative_analysis.relative_improvement.improvement_type
        exp_best = self._get_best_value(exp_trajectory, minimize)
        baseline_final = baseline_trajectory[-1] if baseline_trajectory else float('inf')

        if "objective_value" in improvement_types:
            result.relative_improvement = self.relative_calc.calculate_relative_improvement(
                exp_best, baseline_final, minimize
            )

        if "time_to_target" in improvement_types:
            exp_time = self._extract_runtime(experiment_data)
            baseline_time = self._extract_baseline_runtime(baseline)
            if exp_time is not None and baseline_time is not None:
                result.relative_improvement_time = self.relative_calc.calculate_time_relative_improvement(exp_time, baseline_time)

        if "iteration_to_target" in improvement_types:
            result.relative_improvement_iterations = self.relative_calc.calculate_iteration_relative_improvement(
                exp_trajectory, baseline_trajectory, minimize
            )

    @staticmethod
    def _find_convergence_iteration(trajectory: List[float], minimize: bool) -> int:
        best = min(trajectory) if minimize else max(trajectory)
        for i, value in enumerate(trajectory, 1):
            if (minimize and value <= best) or (not minimize and value >= best):
                return i
        return len(trajectory)

    @staticmethod
    def _warn_on_scale_mismatch(exp_trajectory: List[float], baseline_trajectory: List[float], exp_name: str, baseline_type: str):
        import logging
        if not exp_trajectory or not baseline_trajectory:
            return
        exp_range = max(exp_trajectory) - min(exp_trajectory)
        base_range = max(baseline_trajectory) - min(baseline_trajectory)
        if exp_range > 0 and base_range > 0:
            ratio = max(exp_range, base_range) / min(exp_range, base_range)
            if ratio > 10:
                logging.getLogger(__name__).warning(
                    f"Scale mismatch for {exp_name} vs {baseline_type}: range ratio {ratio:.2f}x"
                )

    def _is_minimizing(self, objective: str) -> bool:
        direction = getattr(self.config, 'optimization_direction', None)
        if direction is None:
            return True
        if isinstance(direction, dict):
            direction = direction.get(objective, OptimizationDirection.MINIMIZE)
        if isinstance(direction, str):
            return direction.lower() in ['minimize', 'min']
        return direction == OptimizationDirection.MINIMIZE

    @staticmethod
    def _get_best_value(trajectory: List[float], minimize: bool) -> float:
        if not trajectory:
            return float('inf') if minimize else float('-inf')
        return min(trajectory) if minimize else max(trajectory)

    @staticmethod
    def _extract_trajectory(experiment_data: Dict[str, Any], objective: str) -> List[float]:
        trajectory = experiment_data.get('trajectory')
        if isinstance(trajectory, dict) and objective in trajectory:
            return trajectory[objective]
        if isinstance(trajectory, list):
            return trajectory

        obj_vals = experiment_data.get('objective_values')
        if isinstance(obj_vals, pd.DataFrame) and objective in obj_vals.columns:
            return obj_vals[objective].tolist()
        if isinstance(obj_vals, dict) and objective in obj_vals:
            return obj_vals[objective]

        return experiment_data.get('best_values', [])

    @staticmethod
    def _extract_baseline_trajectory(
        baseline: BaselineResult,
        objective: str,
        minimize: bool,
        result_key: Optional[str] = None,
    ) -> List[float]:
        return extract_baseline_trajectory(
            baseline,
            objective,
            prefer_cached=True,
            best_so_far_fallback=True,
            minimize=minimize,
            result_key=result_key,
            cache_key=objective,
        )

    @staticmethod
    def _extract_runtime(experiment_data: Dict[str, Any]) -> Optional[float]:
        if 'runtime' in experiment_data:
            return experiment_data['runtime']
        raw = experiment_data.get('raw_experiment')
        if raw and hasattr(raw, 'start_time') and hasattr(raw, 'end_time'):
            try:
                return (raw.end_time - raw.start_time).total_seconds()
            except Exception:
                pass
        return None

    @staticmethod
    def _extract_baseline_runtime(baseline: BaselineResult) -> Optional[float]:
        raw_experiments = getattr(baseline, 'raw_experiments', None)
        if raw_experiments:
            times = []
            for exp in raw_experiments:
                if exp and hasattr(exp, 'start_time') and hasattr(exp, 'end_time'):
                    try:
                        times.append((exp.end_time - exp.start_time).total_seconds())
                    except Exception:
                        continue
            return sum(times) / len(times) if times else None

        raw = baseline.raw_experiment
        if raw and hasattr(raw, 'start_time') and hasattr(raw, 'end_time'):
            try:
                return (raw.end_time - raw.start_time).total_seconds()
            except Exception:
                pass
        return None

    @staticmethod
    def _extract_timestamps(experiment_data: Dict[str, Any], num_points: int) -> Optional[List[float]]:
        timestamps = experiment_data.get('timestamps', None)
        if timestamps:
            return timestamps

        raw = experiment_data.get('raw_experiment')
        if raw and hasattr(raw, 'start_time') and hasattr(raw, 'measured_configurations'):
            try:
                start_time = raw.start_time
                timestamps = []
                for config in raw.measured_configurations[:num_points]:
                    ts = getattr(config, 'iteration_timestamp', None) or getattr(config, 'measured_time', None)
                    if ts:
                        timestamps.append((ts - start_time).total_seconds())
                if len(timestamps) == num_points:
                    return timestamps
            except Exception:
                pass

        runtime = ComparisonProcessor._extract_runtime(experiment_data)
        if runtime is not None and num_points > 0:
            return [runtime * i / (num_points - 1) if num_points > 1 else 0.0 for i in range(num_points)]

        return None

    @staticmethod
    def _extract_baseline_timestamps(baseline: BaselineResult, num_points: int) -> Optional[List[float]]:
        if num_points <= 0:
            return None

        raw = baseline.raw_experiment
        if raw and hasattr(raw, 'start_time') and hasattr(raw, 'measured_configurations'):
            try:
                start_time = raw.start_time
                timestamps = []
                for config in raw.measured_configurations[:num_points]:
                    ts = getattr(config, 'iteration_timestamp', None) or getattr(config, 'measured_time', None)
                    if ts:
                        timestamps.append((ts - start_time).total_seconds())
                if len(timestamps) == num_points:
                    return timestamps
            except Exception:
                pass

        runtime = ComparisonProcessor._extract_baseline_runtime(baseline)
        if runtime is not None and num_points > 0:
            return [runtime * i / (num_points - 1) if num_points > 1 else 0.0 for i in range(num_points)]

        return None
