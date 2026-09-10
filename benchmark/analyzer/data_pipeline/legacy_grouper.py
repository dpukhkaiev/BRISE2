from __future__ import annotations

from typing import Any, Dict, List

from analyzer.config.benchmark_config import CustomGroupingConfig, MatchCondition
from analyzer.data_pipeline.experiment_metadata import ExperimentMetadata
from analyzer.util.grouping_utils import build_group_label, matches_conditions


class ExperimentGrouper:
    """Domain-agnostic grouper for any BRISE serialised Experiment."""

    def __init__(self, config: CustomGroupingConfig):
        self.config = config

    def group(self, experiments: List[Any]) -> Dict[str, List[Any]]:
        """Return ``{group_name: [exp, ...]}`` for all experiments."""
        groups: Dict[str, List[Any]] = {}
        for exp in experiments:
            meta = ExperimentMetadata.extract(exp)
            label = build_group_label(
                meta,
                getattr(exp, "name", "") or "",
                getattr(exp, "_source_filename", None),
                self.config,
            )
            groups.setdefault(label, []).append(exp)
        return groups

    @staticmethod
    def filter(experiments: List[Any], conditions: List[MatchCondition]) -> List[Any]:
        """Return only experiments whose metadata satisfies ALL given conditions."""
        if not conditions:
            return experiments
        return [
            exp for exp in experiments
            if matches_conditions(ExperimentMetadata.extract(exp), conditions)
        ]
