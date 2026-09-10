import json
import logging
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import List, Any, Optional, Dict, Tuple, Iterable

logger = logging.getLogger(__name__)


@dataclass
class SelectableExperiment:
    """Represents an experiment that can be selected as a baseline"""
    name: str
    display_name: str
    description: str
    objectives: List[str]
    iterations: int
    pkl_file: str


@dataclass
class SelectableBaseline:
    """Represents a selectable baseline item (single experiment or grouped)"""
    baseline_id: str
    kind: str
    display_name: str
    description: str
    objectives: List[str]
    iterations: int
    pkl_file: Optional[str] = None
    members: Optional[List[str]] = None


class BaselineSelector:
    """Manages interactive baseline selection from experiment pool"""

    GROUP_PREFIX = "group::"

    def __init__(self, results_dir: Path):
        self.results_dir = Path(results_dir)
        self.selection_file = self.results_dir.parent / "baseline_selection.json"

    def get_selectable_items(self, experiments: List[Any], grouping_config: Optional[Any] = None) -> List[SelectableBaseline]:
        from analyzer.data_pipeline import ExperimentParser, ExperimentGrouper
        parser = ExperimentParser()

        group_items: List[SelectableBaseline] = []
        experiment_items: List[SelectableBaseline] = []

        filtered_experiments = experiments
        if grouping_config is not None and getattr(grouping_config, 'is_configured', False):
            grouped = ExperimentGrouper(grouping_config).group(filtered_experiments)
            for group_label, group_exps in sorted(grouped.items(), key=lambda it: it[0]):
                members = [self._get_exp_name(exp) for exp in group_exps]
                objectives = sorted({obj for exp in group_exps for obj in self._get_objectives(exp)})
                iterations = int(self._avg_iterations(group_exps))
                description = self._build_group_description(len(members), objectives, iterations)
                group_items.append(SelectableBaseline(
                    baseline_id=f"{self.GROUP_PREFIX}{group_label}",
                    kind="group",
                    display_name=group_label,
                    description=description,
                    objectives=objectives,
                    iterations=iterations,
                    members=members,
                ))

        for exp in filtered_experiments:
            name = self._get_exp_name(exp)
            objectives = self._get_objectives(exp)
            iterations = len(getattr(exp, 'measured_configurations', []))

            if iterations > 0 and objectives:
                display_name = parser.build_display_name(name)
                description = self._build_description(name, objectives, iterations)
                experiment_items.append(SelectableBaseline(
                    baseline_id=name,
                    kind="experiment",
                    display_name=display_name,
                    description=description,
                    objectives=objectives,
                    iterations=iterations,
                    pkl_file=getattr(exp, '_source_filename', f"{name}.pkl"),
                ))

        return group_items + experiment_items

    def get_selectable_items_stream(
        self,
        experiment_batches: Iterable[List[Any]],
        grouping_config: Optional[Any] = None,
        enable_grouping: bool = False,
    ) -> List[SelectableBaseline]:
        from analyzer.data_pipeline import ExperimentParser
        from analyzer.data_pipeline.experiment_metadata import ExperimentMetadata
        from analyzer.util.grouping_utils import build_group_label

        parser = ExperimentParser()
        experiment_items: List[SelectableBaseline] = []
        group_items: List[SelectableBaseline] = []
        group_acc: Dict[str, Dict[str, Any]] = {}

        do_grouping = enable_grouping or (
            grouping_config is not None and getattr(grouping_config, 'is_configured', False)
        )

        for batch in experiment_batches:
            for exp in batch:
                meta = ExperimentMetadata.extract(exp)
                name = self._get_exp_name(exp)
                objectives = self._get_objectives(exp)
                iterations = len(getattr(exp, 'measured_configurations', []))
                if iterations > 0 and objectives:
                    display_name = parser.build_display_name(name)
                    description = self._build_description(name, objectives, iterations)
                    experiment_items.append(SelectableBaseline(
                        baseline_id=name,
                        kind="experiment",
                        display_name=display_name,
                        description=description,
                        objectives=objectives,
                        iterations=iterations,
                        pkl_file=getattr(exp, '_source_filename', f"{name}.pkl"),
                    ))

                if do_grouping:
                    label = build_group_label(meta, name, getattr(exp, '_source_filename', None), grouping_config)
                    group = group_acc.setdefault(label, {
                        'members': [],
                        'objectives': set(),
                        'iterations': 0,
                        'count': 0,
                    })
                    group['members'].append(name)
                    group['objectives'].update(objectives)
                    group['iterations'] += iterations
                    group['count'] += 1

        for group_label, group in sorted(group_acc.items(), key=lambda it: it[0]):
            count = group['count']
            if count == 0:
                continue
            objectives = sorted(group['objectives'])
            avg_iterations = int(group['iterations'] / count)
            description = self._build_group_description(len(group['members']), objectives, avg_iterations)
            group_items.append(SelectableBaseline(
                baseline_id=f"{self.GROUP_PREFIX}{group_label}",
                kind="group",
                display_name=group_label,
                description=description,
                objectives=objectives,
                iterations=avg_iterations,
                members=group['members'],
            ))

        return group_items + experiment_items

    def get_selectable_experiments(self, experiments: List[Any]) -> List[SelectableExperiment]:
        """Backward-compatible experiment-only list (legacy UI)."""
        items = self.get_selectable_items(experiments, grouping_config=None)
        return [
            SelectableExperiment(
                name=item.baseline_id,
                display_name=item.display_name,
                description=item.description,
                objectives=item.objectives,
                iterations=item.iterations,
                pkl_file=item.pkl_file or f"{item.baseline_id}.pkl",
            )
            for item in items
            if item.kind == "experiment"
        ]

    def resolve_selection(
        self,
        selected_ids: List[str],
        experiments: List[Any],
        grouping_config: Optional[Any] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, List[Any]]]:
        """Resolve selected ids into experiment and grouped baseline mappings."""
        from analyzer.util.grouping_utils import matches_conditions

        filtered_experiments = experiments
        if grouping_config is not None and getattr(grouping_config, 'is_configured', False):
            from analyzer.data_pipeline import ExperimentGrouper
            group_map = ExperimentGrouper(grouping_config).group(experiments)
            grouped = {label: exps for label, exps in group_map.items()}

        name_to_exp = {self._get_exp_name(exp): exp for exp in filtered_experiments}

        selected_experiments: Dict[str, Any] = {}
        selected_groups: Dict[str, List[Any]] = {}

        for selected_id in selected_ids:
            if selected_id.startswith(self.GROUP_PREFIX):
                label = selected_id[len(self.GROUP_PREFIX):]
                if label in grouped:
                    selected_groups[label] = grouped[label]
                else:
                    logger.warning("Selected baseline group '%s' not found in current grouping", label)
                continue

            exp = name_to_exp.get(selected_id)
            if exp is not None:
                selected_experiments[selected_id] = exp
            else:
                logger.warning("Selected baseline experiment '%s' not found", selected_id)

        return selected_experiments, selected_groups

    def resolve_selection_stream(
        self,
        selected_ids: List[str],
        experiment_batches: Iterable[List[Any]],
        grouping_config: Optional[Any] = None,
        enable_grouping: bool = False,
    ) -> Tuple[Dict[str, Any], Dict[str, List[Any]]]:
        from analyzer.data_pipeline.experiment_metadata import ExperimentMetadata
        from analyzer.util.grouping_utils import build_group_label, matches_conditions

        filter_conditions = []

        selected_experiments: Dict[str, Any] = {}
        selected_groups: Dict[str, List[Any]] = {}

        do_grouping = enable_grouping or (
            grouping_config is not None and getattr(grouping_config, 'is_configured', False)
        )

        group_labels = {
            sid[len(self.GROUP_PREFIX):]
            for sid in selected_ids
            if sid.startswith(self.GROUP_PREFIX)
        }
        selected_exp_ids = {sid for sid in selected_ids if not sid.startswith(self.GROUP_PREFIX)}

        for batch in experiment_batches:
            for exp in batch:
                meta = ExperimentMetadata.extract(exp)
                if filter_conditions and not matches_conditions(meta, filter_conditions):
                    continue

                name = self._get_exp_name(exp)
                if name in selected_exp_ids:
                    selected_experiments[name] = exp

                if group_labels and do_grouping:
                    label = build_group_label(meta, name, getattr(exp, '_source_filename', None), grouping_config)
                    if label in group_labels:
                        selected_groups.setdefault(label, []).append(exp)

        for label in group_labels:
            if label not in selected_groups:
                logger.warning("Selected baseline group '%s' not found in current grouping", label)

        for name in selected_exp_ids:
            if name not in selected_experiments:
                logger.warning("Selected baseline experiment '%s' not found", name)

        return selected_experiments, selected_groups

    def save_selection(self, selected_names: List[str]):
        with open(self.selection_file, 'w') as f:
            json.dump({'selected_baselines': selected_names, 'timestamp': datetime.now().isoformat()}, f, indent=2)
        logger.info(f"Saved baseline selection: {selected_names}")

    def load_selection(self) -> Optional[List[str]]:
        if not self.selection_file.exists():
            return None
        try:
            with open(self.selection_file, 'r') as f:
                return json.load(f).get('selected_baselines', [])
        except Exception as e:
            logger.error(f"Failed to load baseline selection: {e}")
            return None

    def clear_selection(self):
        if self.selection_file.exists():
            self.selection_file.unlink()

    def has_selection(self) -> bool:
        return self.selection_file.exists()

    @staticmethod
    def _get_exp_name(exp: Any) -> str:
        return getattr(exp, 'name', None) or getattr(exp, 'ed_id', None) or 'experiment'

    @staticmethod
    def _avg_iterations(experiments: List[Any]) -> float:
        counts = [len(getattr(exp, 'measured_configurations', [])) for exp in experiments]
        return sum(counts) / len(counts) if counts else 0.0

    @staticmethod
    def _get_objectives(exp: Any) -> List[str]:
        measured_configs = getattr(exp, 'measured_configurations', [])
        if not measured_configs:
            return []
        first_config = measured_configs[0]
        results = getattr(first_config, 'averaged_result', None) or getattr(first_config, 'results', {})
        return list(results.keys()) if hasattr(results, 'keys') else []

    @staticmethod
    def _build_group_description(count: int, objectives: List[str], avg_iterations: int) -> str:
        obj_str = (
            f"{len(objectives)} objective{'s' if len(objectives) != 1 else ''}"
            f" ({', '.join(objectives[:3])}{'...' if len(objectives) > 3 else ''})"
        )
        return f"{count} experiments | {obj_str} | ~{avg_iterations} iterations"

    @staticmethod
    def _build_description(full_name: str, objectives: List[str], iterations: int) -> str:
        parts = full_name.replace('exp_', '').split('_')
        skip = {'test', 'case', 'wo', 'dch'}
        descriptors = [
            p.upper() if len(p) <= 4 else p.capitalize()
            for p in parts if not p.isdigit() and p not in skip and len(p) > 1
        ]
        obj_str = f"{len(objectives)} objective{'s' if len(objectives) != 1 else ''} ({', '.join(objectives[:3])}{'...' if len(objectives) > 3 else ''})"
        components = [' • '.join(descriptors[:5]), obj_str, f"{iterations} iterations"]
        return ' | '.join(components)
