import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from analyzer.util.trajectory_utils import extract_best_so_far_series, extract_group_best_so_far_series


logger = logging.getLogger(__name__)


@dataclass
class BaselineResult:
    """Container for baseline experiment results"""
    baseline_id: str
    baseline_type: str
    trajectory: Union[List[float], Dict[str, List[float]]]
    best_value: float
    raw_experiment: Optional[Any] = None
    raw_experiments: Optional[List[Any]] = None

    @staticmethod
    def from_experiment(experiment: Any, baseline_type: str, objective: Optional[str] = None) -> "BaselineResult":
        trajectory = BaselineResult._extract_trajectory(experiment, objective)
        best_value = trajectory[-1] if trajectory else float('inf')
        return BaselineResult(
            baseline_id=f"baseline_{baseline_type}",
            baseline_type=baseline_type,
            trajectory=trajectory,
            best_value=best_value,
            raw_experiment=experiment
        )

    @staticmethod
    def from_experiments_group(experiments: List[Any], baseline_type: str, objective: Optional[str] = None) -> "BaselineResult":
        traj_map: Dict[str, List[float]] = {}
        best_value = float('inf')
        if objective:
            grouped = extract_group_best_so_far_series(experiments, objective=objective, minimize=True)
            traj_map[objective] = grouped
            best_value = grouped[-1] if grouped else float('inf')
        representative = experiments[0] if experiments else None
        return BaselineResult(
            baseline_id=f"baseline_{baseline_type}",
            baseline_type=baseline_type,
            trajectory=traj_map,
            best_value=best_value,
            raw_experiment=representative,
            raw_experiments=experiments,
        )

    @staticmethod
    def _extract_trajectory(experiment: Any, objective: Optional[str] = None) -> List[float]:
        measured_configs = getattr(experiment, 'measured_configurations', [])
        if not measured_configs:
            logger.warning("No measured_configurations found in baseline experiment")
            return []

        return extract_best_so_far_series(
            experiment,
            objective=objective,
            minimize=True,
            only_enabled_improves=False,
        )


class BaselineManager:
    """Loads and caches baseline experiments for comparative analysis"""

    def __init__(self, results_dir: Path, benchmark_id: Optional[str] = None):
        self.results_dir = Path(results_dir)
        self.benchmark_id = benchmark_id
        self._cache: Dict[str, BaselineResult] = {}
        self._user_selected_experiments: Dict[str, Any] = {}
        self._user_selected_groups: Dict[str, List[Any]] = {}

    def load_baseline(self, baseline_type: str) -> Optional[BaselineResult]:
        if baseline_type in self._cache:
            return self._cache[baseline_type]

        if baseline_type in self._user_selected_experiments:
            result = BaselineResult.from_experiment(self._user_selected_experiments[baseline_type], baseline_type)
            self._cache[baseline_type] = result
            return result

        if baseline_type in self._user_selected_groups:
            result = BaselineResult.from_experiments_group(self._user_selected_groups[baseline_type], baseline_type)
            self._cache[baseline_type] = result
            return result

        return None

    def register_user_baseline(self, experiment: Any, baseline_name: str):
        self._user_selected_experiments[baseline_name] = experiment

    def register_user_baseline_group(self, experiments: List[Any], baseline_name: str):
        self._user_selected_groups[baseline_name] = experiments

    def get_available_baseline_types(self) -> List[str]:
        return list(self._user_selected_experiments.keys()) + list(self._user_selected_groups.keys())