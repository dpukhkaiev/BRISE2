import math
from typing import Any, List, Optional, Set, Dict, Tuple

from analyzer.config import MetricType


class MetricExtractor:
    """Extracts metrics and objectives from experiments"""

    # Tracks (objective, llh_path) pairs already warned about, so the
    # "no values filled" LLH warning is logged once per config, not per experiment.
    _llh_empty_warned: Set[Tuple[str, str]] = set()

    @staticmethod
    def discover_objectives(experiments: List[Any]) -> Set[str]:
        """Discover all objective keys from experiments"""
        objectives = set()
        for exp in experiments:
            configs = getattr(exp, 'measured_configurations', [])[:5]
            for conf in configs:
                results = getattr(conf, 'results', {})
                for key, value in results.items():
                    if MetricExtractor._is_valid_numeric(value):
                        objectives.add(key)
        return objectives

    @staticmethod
    def _is_valid_numeric(value: Any) -> bool:
        return isinstance(value, (int, float)) and not math.isnan(value)

    @staticmethod
    def extract_objective_series(exp: Any, objective: str) -> List[float]:
        """Extract best-so-far objective series from experiment (cumulative minimum)"""
        values: List[float] = []
        current_best: Optional[float] = None

        for conf in getattr(exp, 'measured_configurations', []):
            results = getattr(conf, 'results', {})
            is_enabled = getattr(conf, 'is_enabled', True)
            val = results.get(objective) if results else None
            if val is not None and MetricExtractor._is_valid_numeric(val):
                fval = float(val)
                if current_best is None:
                    current_best = fval
                elif is_enabled and fval < current_best:
                    current_best = fval
                values.append(current_best)

        return values

    @staticmethod
    def extract_llh_series(
        exp: Any,
        objective: str,
        llh_path: str,
        name_mapping: Dict[str, str],
    ) -> Dict[str, List[Optional[float]]]:
        """Extract per-LLH sparse objective series from an HH experiment.

        For each configuration measurement, looks up the selected LLH via
        ``llh_path`` in the hyperparameters dict, maps it to a display name via
        ``name_mapping``, and records the raw objective value at that iteration.
        Returns a dict ``{display_name: series}`` where ``series[i]`` is the
        objective value if that LLH was selected at iteration i, else ``None``.
        """
        import logging as _logging
        _log = _logging.getLogger(__name__)

        display_names = list(name_mapping.values())
        cfgs = getattr(exp, 'measured_configurations', [])
        n = len(cfgs)
        result: Dict[str, List[Optional[float]]] = {name: [None] * n for name in display_names}

        unknown_llh_values: set = set()
        filled = 0

        for i, conf in enumerate(cfgs):
            # Prefer the private backing field: when core_entities is unavailable at
            # unpickle time, the `hyperparameters` property is not callable but
            # `_hyperparameters` (the OrderedDict) is still restored from __dict__.
            hp = getattr(conf, '_hyperparameters', None) or getattr(conf, 'hyperparameters', None)
            if hp is None:
                continue
            # Normalise to plain dict — handles dict, OrderedDict, and ConfigSpace Configuration
            if not isinstance(hp, dict):
                try:
                    hp = dict(hp)
                except (TypeError, ValueError):
                    continue
            llh_raw = hp.get(llh_path)
            if llh_raw is None:
                continue
            display = name_mapping.get(str(llh_raw))
            if display is None:
                unknown_llh_values.add(str(llh_raw))
                continue
            results_dict = getattr(conf, 'results', {})
            val = results_dict.get(objective) if results_dict else None
            if val is not None and MetricExtractor._is_valid_numeric(val):
                result[display][i] = float(val)
                filled += 1

        if filled == 0 and n > 0:
            warn_key = (objective, llh_path)
            if warn_key not in MetricExtractor._llh_empty_warned:
                MetricExtractor._llh_empty_warned.add(warn_key)
                _log.warning(
                    "extract_llh_series: no values filled for objective=%r llh_path=%r "
                    "(n_configs=%d, unknown_llh=%s). "
                    "Check that the hyperparameter path and name mapping are correct. "
                    "(further identical warnings for this config suppressed)",
                    objective, llh_path, n, unknown_llh_values or "(none found)",
                )
        elif unknown_llh_values:
            _log.debug(
                "extract_llh_series: unrecognised LLH values (not in name_mapping): %s",
                unknown_llh_values,
            )

        return result

    @staticmethod
    def extract_raw_objective_series(exp: Any, objective: str) -> List[float]:
        """Extract raw (non-cumulative) objective values per measured configuration."""
        values: List[float] = []
        for conf in getattr(exp, 'measured_configurations', []):
            results = getattr(conf, 'results', {})
            val = results.get(objective) if results else None
            if val is not None and MetricExtractor._is_valid_numeric(val):
                values.append(float(val))
        return values

    @staticmethod
    def extract_time_series(exp: Any) -> List[Optional[float]]:
        """Extract time series from experiment using iteration timestamps"""
        times = []
        start_time = getattr(exp, 'start_time', None)

        for conf in getattr(exp, 'measured_configurations', []):
            time_val = MetricExtractor._calculate_time_delta(conf, start_time)
            times.append(time_val)

        return times

    @staticmethod
    def _calculate_time_delta(conf: Any, start_time: Any) -> Optional[float]:
        if not hasattr(conf, 'iteration_timestamp') or not start_time:
            return None
        try:
            delta = conf.iteration_timestamp - start_time
            return delta.total_seconds()
        except Exception:
            return None

    @staticmethod
    def extract_runtime(exp: Any) -> Optional[float]:
        if not (hasattr(exp, 'start_time') and hasattr(exp, 'end_time')):
            return None
        try:
            delta = exp.end_time - exp.start_time
            return delta.total_seconds()
        except Exception:
            return None

    @staticmethod
    def extract_grouped_data(experiments: List[Any], objective: str,
            metric_type: str = MetricType.ITERATION.value) -> Dict[str, Any]:
        """Extract min/max/mean objective values across grouped test case repetitions.

        Shorter repetitions are NOT forward-filled. At each iteration index we
        aggregate only over the repetitions that still have real data there; the
        returned ``sample_counts`` lets downstream code filter sparsely-sampled
        indices.

        Returns:
            Dict with min_values, max_values, mean_values, std_values,
            sample_counts and metric_values (all aligned by index).
        """
        if not experiments:
            return {}

        all_series = [MetricExtractor.extract_objective_series(exp, objective) for exp in experiments]
        all_series = [s for s in all_series if s]

        if not all_series:
            return {}

        all_time_series = []
        if metric_type == MetricType.TIME.value:
            all_time_series = [MetricExtractor.extract_time_series(exp) for exp in experiments]

        max_length = max(len(s) for s in all_series)
        min_values, max_values, mean_values, std_values, sample_counts = (
            MetricExtractor._compute_statistics(all_series, max_length)
        )
        metric_values = MetricExtractor._generate_metric_values(metric_type, max_length, all_time_series)

        return {'min_values': min_values, 'max_values': max_values, 'mean_values': mean_values,
                'std_values': std_values, 'sample_counts': sample_counts,
                'metric_values': metric_values}

    @staticmethod
    def extract_grouped_series_data(
        series_list: List[List[float]],
        metric_type: str = MetricType.ITERATION.value,
        time_series_list: Optional[List[List[Optional[float]]]] = None,
    ) -> Dict[str, Any]:
        if not series_list:
            return {}

        all_series = [s for s in series_list if s]
        if not all_series:
            return {}

        max_length = max(len(s) for s in all_series)
        min_values, max_values, mean_values, std_values, sample_counts = (
            MetricExtractor._compute_statistics(all_series, max_length)
        )

        time_series_list = time_series_list or []
        metric_values = MetricExtractor._generate_metric_values(metric_type, max_length, time_series_list)

        return {
            'min_values': min_values,
            'max_values': max_values,
            'mean_values': mean_values,
            'std_values': std_values,
            'sample_counts': sample_counts,
            'metric_values': metric_values,
        }

    @staticmethod
    def _compute_statistics(series_list: List[List[float]], length: int) -> Tuple[
        List[Optional[float]], List[Optional[float]], List[Optional[float]],
        List[Optional[float]], List[int]]:
        """Compute min, max, mean, std-dev and per-index sample count.

        Reps shorter than ``length`` contribute NaN at indices past their end, so
        nanmean/nanstd aggregate only over reps that actually reached that index.
        """
        import numpy as np
        arr = np.full((len(series_list), length), np.nan, dtype=float)
        for row, s in enumerate(series_list):
            for col, v in enumerate(s):
                if v is not None:
                    arr[row, col] = float(v)

        def _to_list(a: np.ndarray) -> List[Optional[float]]:
            return [None if np.isnan(v) else float(v) for v in a]

        sample_counts = (~np.isnan(arr)).sum(axis=0).astype(int).tolist()

        # Suppress "Mean of empty slice" / "Degrees of freedom <= 0" warnings at
        # indices with zero samples — those become NaN -> None in the output.
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            return (
                _to_list(np.nanmin(arr, axis=0)),
                _to_list(np.nanmax(arr, axis=0)),
                _to_list(np.nanmean(arr, axis=0)),
                _to_list(np.nanstd(arr, axis=0)),
                sample_counts,
            )

    @staticmethod
    def _generate_metric_values(metric_type: str, length: int, time_series_list: List[List[Optional[float]]]) -> List[
        Optional[float]]:
        if metric_type == MetricType.TIME.value and time_series_list:
            metric_values = []
            for i in range(length):
                times_at_i = [ts[i] for ts in time_series_list if i < len(ts) and ts[i] is not None]
                if times_at_i:
                    metric_values.append(sum(times_at_i) / len(times_at_i))
                else:
                    metric_values.append(None)
            return metric_values
        return list(range(length))
