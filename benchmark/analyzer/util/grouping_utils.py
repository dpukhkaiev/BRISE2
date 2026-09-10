import re
from typing import Any, Dict, List, Optional

from analyzer.config.benchmark_config import CustomGroupingConfig, MatchCondition


def compute_rep_threshold(
    min_reps: int,
    min_reps_ratio: Optional[float],
    sample_counts: List[Optional[int]],
) -> int:
    """Return the minimum number of repetitions required at an iteration index.

    When *min_reps_ratio* is set (0 < ratio ≤ 1) the threshold is
    ``max(1, round(max_count * min_reps_ratio))`` so the cut-off adapts to
    the actual group size.  Otherwise the threshold is simply *min_reps*.
    """
    if min_reps_ratio is not None and 0.0 < min_reps_ratio <= 1.0:
        real_counts = [c for c in sample_counts if c is not None and c > 0]
        n_reps = max(real_counts) if real_counts else 1
        return max(1, round(n_reps * min_reps_ratio))
    return max(1, int(min_reps))

_DUPLICATE_SUFFIX_RE = re.compile(r'(\(\d+\))+$')
_REPETITION_SUFFIX_RE = re.compile(r'_(\d+)$')


def matches_conditions(meta: Dict[str, Any], conditions: List[MatchCondition]) -> bool:
    if not conditions:
        return True
    return all(_condition_matches(meta, cond) for cond in conditions)


def _condition_matches(meta: Dict[str, Any], cond: MatchCondition) -> bool:
    from analyzer.data_pipeline.experiment_metadata import ExperimentMetadata
    extracted = ExperimentMetadata.get(meta, cond.path)

    if isinstance(extracted, list):
        extracted_str = ",".join(str(v) for v in extracted)
    else:
        extracted_str = str(extracted) if extracted is not None else ""

    if cond.pattern is not None:
        return bool(re.search(cond.pattern, extracted_str))

    if cond.value is None:
        return bool(extracted_str)

    if cond.contains:
        return cond.value in extracted_str

    return extracted_str == cond.value


def _find_value_group_label(meta: Dict[str, Any], grouping_config: CustomGroupingConfig) -> str:
    from analyzer.data_pipeline.experiment_metadata import ExperimentMetadata
    for path, value_map in grouping_config._value_lookup.items():
        extracted = ExperimentMetadata.get(meta, path)
        if extracted is None:
            continue
        if isinstance(extracted, list):
            for item in extracted:
                mapped = value_map.get(str(item))
                if mapped:
                    return mapped
            continue
        mapped = value_map.get(str(extracted))
        if mapped:
            return mapped
    return ""


def build_group_label(
    meta: Dict[str, Any],
    exp_name: str,
    source_filename: Optional[str],
    grouping_config: Optional[CustomGroupingConfig],
) -> str:
    if grouping_config is not None and getattr(grouping_config, 'is_configured', False):
        mapped = _find_value_group_label(meta, grouping_config)
        if mapped:
            return mapped

    base_name = source_filename or exp_name or "experiment"
    if base_name.endswith('.pkl'):
        base_name = base_name[:-4]
    base_name = _DUPLICATE_SUFFIX_RE.sub("", base_name)
    base_name = _REPETITION_SUFFIX_RE.sub("", base_name)
    return base_name
