from __future__ import annotations

import math
from typing import Any, List, Optional


def is_valid_numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not math.isnan(value)

def extract_result_value(results: Any, objective: str) -> Optional[float]:
    if not results:
        return None
    if hasattr(results, 'get'):
        value = results.get(objective)
        if value is None and hasattr(results, 'keys'):
            keys = list(results.keys())
            value = results[keys[0]] if keys else None
    else:
        value = None

    if value is None or not is_valid_numeric(value):
        return None
    return float(value)

def extract_raw_objective_series(exp: Any, objective: str) -> List[float]:
    values: List[float] = []
    for conf in getattr(exp, 'measured_configurations', []):
        results = getattr(conf, 'averaged_result', None) or getattr(conf, 'results', None) or {}
        value = extract_result_value(results, objective)
        if value is not None:
            values.append(value)
    return values

def extract_best_so_far_series(
    exp: Any,
    objective: str,
    minimize: bool = True,
    only_enabled_improves: bool = True,
) -> List[float]:
    values: List[float] = []
    current_best: Optional[float] = None

    for conf in getattr(exp, 'measured_configurations', []):
        results = getattr(conf, 'averaged_result', None) or getattr(conf, 'results', None) or {}
        value = extract_result_value(results, objective)
        if value is None:
            continue

        if current_best is None:
            current_best = value
        else:
            can_improve = getattr(conf, 'is_enabled', True) if only_enabled_improves else True
            if can_improve:
                current_best = min(current_best, value) if minimize else max(current_best, value)
        values.append(current_best)

    return values


def extract_group_best_so_far_series(
    experiments: List[Any],
    objective: str,
    minimize: bool = True,
) -> List[float]:
    trajectories = [
        extract_best_so_far_series(exp, objective, minimize=minimize, only_enabled_improves=False)
        for exp in experiments
    ]
    return aggregate_trajectories(trajectories)


def _pad_trajectories(trajectories: List[List[float]]) -> List[List[float]]:
    if not trajectories:
        return []
    max_len = max((len(t) for t in trajectories), default=0)
    padded: List[List[float]] = []
    for traj in trajectories:
        if not traj:
            padded.append([])
            continue
        if len(traj) < max_len:
            padded.append(traj + [traj[-1]] * (max_len - len(traj)))
        else:
            padded.append(traj)
    return padded


def aggregate_trajectories(trajectories: List[List[float]]) -> List[float]:
    """Aggregate multiple trajectories by index-wise mean (ignoring missing values).

    Trajectories are padded with their last value to keep best-so-far sequences monotonic.
    """
    if not trajectories:
        return []

    padded = _pad_trajectories([t for t in trajectories if t])
    if not padded:
        return []

    max_len = max((len(t) for t in padded), default=0)
    aggregated: List[float] = []
    for idx in range(max_len):
        values = [t[idx] for t in padded if idx < len(t) and is_valid_numeric(t[idx])]
        if values:
            aggregated.append(sum(values) / len(values))
    return aggregated


def extract_baseline_trajectory(
    baseline: Any,
    objective: str,
    prefer_cached: bool = True,
    best_so_far_fallback: bool = True,
    minimize: bool = True,
    result_key: Optional[str] = None,
    cache_key: Optional[str] = None,
) -> List[float]:
    cached = getattr(baseline, 'trajectory', None)
    key = cache_key or objective
    if isinstance(cached, dict):
        if key in cached:
            return [float(v) for v in cached[key] if v is not None and is_valid_numeric(v)]
        # Dict exists but key not found — fall through to raw_experiments
    elif prefer_cached and cached and not all(v == float('inf') for v in cached):
        return [float(v) for v in cached if v is not None and is_valid_numeric(v)]

    raw_experiments = getattr(baseline, 'raw_experiments', None)
    if raw_experiments:
        series_key = result_key or objective
        filtered_experiments = raw_experiments
        try:
            from analyzer.data_pipeline.experiment_metadata import ExperimentMetadata
            instance_matches = [exp for exp in raw_experiments
                                if ExperimentMetadata.extract(exp).get("problem_instance") == objective]
            if instance_matches:
                filtered_experiments = instance_matches
        except Exception:
            pass

        grouped = extract_group_best_so_far_series(filtered_experiments, series_key, minimize=minimize)
        if isinstance(cached, dict):
            cached[key] = grouped
        else:
            try:
                baseline.trajectory = {key: grouped}
            except Exception:
                pass
        return grouped

    raw_experiment = getattr(baseline, 'raw_experiment', None)
    if raw_experiment is None:
        return []

    series_key = result_key or objective
    if best_so_far_fallback:
        return extract_best_so_far_series(raw_experiment, series_key, minimize=minimize, only_enabled_improves=False)
    return extract_raw_objective_series(raw_experiment, series_key)
