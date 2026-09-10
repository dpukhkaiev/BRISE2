from typing import List, Optional

from analyzer.config import NormalizationType, OptimizationDirection


class DataProcessor:
    """Processes and normalizes data series"""

    @staticmethod
    def normalize_series(series_list: List[List[float]], method: str) -> List[List[float]]:
        """Normalize series based on strategy"""
        if method == NormalizationType.NONE.value:
            return series_list

        if method == NormalizationType.MIN_OVER_ALL.value:
            return DataProcessor._normalize_by_global_min(series_list)

        if method == NormalizationType.MAX_OVER_ALL.value:
            return DataProcessor._normalize_by_global_max(series_list)

        return series_list

    @staticmethod
    def _normalize_by_global_min(series_list: List[List[float]]) -> List[List[float]]:
        """Normalize all series by global minimum value"""
        all_mins = [min([y for y in s if y is not None], default=None) for s in series_list]
        global_min = min([m for m in all_mins if m is not None], default=None)

        if global_min is None or global_min == 0:
            return series_list

        return [[(y / global_min) if y is not None else None for y in series] for series in series_list]

    @staticmethod
    def _normalize_by_global_max(series_list: List[List[float]]) -> List[List[float]]:
        """Normalize all series by global maximum value"""
        all_maxes = [max([y for y in s if y is not None], default=None) for s in series_list]
        global_max = max([m for m in all_maxes if m is not None], default=None)

        if global_max is None or global_max == 0:
            return series_list

        return [[(y / global_max) if y is not None else None for y in series] for series in series_list]

    @staticmethod
    def compute_best_so_far(values: List[Optional[float]], direction: str = OptimizationDirection.MINIMIZE.value) -> \
    List[Optional[float]]:
        best_series = []
        current_best = None

        for val in values:
            if val is None:
                best_series.append(current_best)
                continue

            if current_best is None:
                current_best = val
            else:
                if direction == OptimizationDirection.MINIMIZE.value:
                    current_best = min(current_best, val)
                else:
                    current_best = max(current_best, val)

            best_series.append(current_best)

        return best_series
