import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from analyzer.data_pipeline import ExperimentParser
from analyzer.data_pipeline.experiment_metadata import ExperimentMetadata
from analyzer.data_pipeline.metric_extractor import MetricExtractor
from analyzer.orchestration.analysis_services import ObjectivePartitionService
from analyzer.util.trajectory_utils import extract_group_best_so_far_series, aggregate_trajectories
from analyzer.util.grouping_utils import build_group_label, compute_rep_threshold

from analyzer.config import BenchmarkConfig
from analyzer.comparison import BaselineManager, ComparisonProcessor

logger = logging.getLogger(__name__)


class ComparativeAnalysisOrchestrator:
    """Orchestrates comparative benchmarking analysis"""

    def __init__(self, config: BenchmarkConfig, benchmark_id: Optional[str] = None):
        self.config = config
        self.benchmark_id = benchmark_id
        self.results_dir = Path(config.results_folder)
        self.parser = ExperimentParser()
        self.extractor = MetricExtractor()
        self.baseline_manager = BaselineManager(self.results_dir, benchmark_id)
        self.comparison_processor = ComparisonProcessor(config)

    def load_baseline_experiments(self) -> Dict[str, Any]:
        baselines = {}
        for baseline_type in self.baseline_manager.get_available_baseline_types():
            baseline = self.baseline_manager.load_baseline(baseline_type)
            if baseline:
                baselines[baseline_type] = baseline
                logger.info(f"Loaded baseline: {baseline_type}")
        return baselines

    def compute_comparative_metrics(self, experiments: List[Any], baselines: Dict[str, Any]) -> Dict[str, List[Any]]:
        if not baselines:
            return {}

        partition_service = ObjectivePartitionService(self.extractor)
        grouping_config = self._get_comparative_grouping_config()
        use_grouping = grouping_config is not None and getattr(grouping_config, 'is_configured', False)

        objective_partitions = partition_service.partition(self.config.objectives_to_measure, experiments)
        if not objective_partitions:
            return {}

        comparisons: Dict[str, List[Any]] = {}

        for objective, partition_experiments in objective_partitions.items():
            if not partition_experiments:
                continue

            result_key = partition_service.resolve_result_key(objective, partition_experiments)
            objective_comparisons = []

            if use_grouping:
                from analyzer.data_pipeline import ExperimentGrouper
                grouped = ExperimentGrouper(grouping_config).group(partition_experiments)
                minimize = self.comparison_processor._is_minimizing(objective)
                for group_label, group_exps in grouped.items():
                    if not group_exps:
                        continue
                    exp_trajectory = extract_group_best_so_far_series(group_exps, result_key, minimize=minimize)
                    if not exp_trajectory:
                        continue
                    representative = group_exps[0]
                    experiment_data = {
                        'name': group_label,
                        'display_name': group_label,
                        'trajectory': {objective: exp_trajectory},
                        'objective_values': {objective: exp_trajectory},
                        'raw_experiment': representative,
                        'runtime': self._avg_runtime(group_exps, self.extractor),
                    }
                    matching = self._select_matching_baselines(representative, group_label, baselines)
                    objective_comparisons.extend(
                        self._compare_against_baselines(experiment_data, group_label, objective, result_key, matching)
                    )
                if objective_comparisons:
                    comparisons[objective] = objective_comparisons
                continue

            for exp in partition_experiments:
                try:
                    exp_name = getattr(exp, 'name', None) or getattr(exp, 'ed_id', 'unknown')
                    exp_trajectory = self.extractor.extract_objective_series(exp, result_key)
                    if not exp_trajectory:
                        continue
                    experiment_data = {
                        'name': exp_name,
                        'display_name': self.parser.build_display_name(exp_name),
                        'trajectory': {objective: exp_trajectory},
                        'objective_values': {objective: exp_trajectory},
                        'raw_experiment': exp,
                        'runtime': self.extractor.extract_runtime(exp),
                    }
                    matching = self._select_matching_baselines(exp, exp_name, baselines)
                    objective_comparisons.extend(
                        self._compare_against_baselines(experiment_data, exp_name, objective, result_key, matching)
                    )
                except Exception as e:
                    logger.error(f"Failed to process experiment: {e}")

            if objective_comparisons:
                comparisons[objective] = objective_comparisons

        return comparisons

    def compute_comparative_metrics_streaming(
        self,
        series_by_objective: Dict[str, List[Any]],
        baselines: Dict[str, Any],
        result_keys: Dict[str, str],
        grouping_config: Optional[Any] = None,
    ) -> Dict[str, List[Any]]:
        if not baselines:
            return {}

        cached_baseline_info = {}
        for baseline_key, baseline in baselines.items():
            baseline_exp = getattr(baseline, 'raw_experiment', None)
            bl_meta = ExperimentMetadata.extract(baseline_exp) if baseline_exp is not None else {}
            bl_name = self._baseline_name(baseline_key, baseline)
            cached_baseline_info[baseline_key] = {
                'task': self._normalize_key(bl_meta.get("task_name", "")),
                'identifier': self._normalize_key(bl_name),
                'display': self._normalize_key(self.parser.build_display_name(bl_name)),
            }

        use_grouping = grouping_config is not None and getattr(grouping_config, 'is_configured', False)
        comparisons: Dict[str, List[Any]] = {}

        for objective, series_items in series_by_objective.items():
            if not series_items:
                continue

            result_key = result_keys.get(objective, objective)
            objective_comparisons = []

            if use_grouping:
                known_groups = grouping_config.known_group_names
                grouped: Dict[str, Dict[str, Any]] = {}
                for item in series_items:
                    label = build_group_label(item.metadata, item.name, item.source_filename, grouping_config)
                    if label not in known_groups:
                        continue
                    group = grouped.setdefault(label, {
                        'series_list': [],
                        'time_series_list': [],
                        'runtimes': [],
                        'meta': item.metadata,
                    })
                    group['series_list'].append(item.series)
                    if item.time_series:
                        group['time_series_list'].append(item.time_series)
                    if item.runtime is not None:
                        group['runtimes'].append(item.runtime)

                ordered = grouping_config.ordered_group_names
                grouped = {k: grouped[k] for k in ordered if k in grouped}

                # Use the same min_reps / min_reps_ratio that the convergence plot uses so
                # the trajectory fed to the regret calculator is trimmed identically.
                _min_reps, _min_reps_ratio = 1, None
                for _plot in self.config.plots:
                    if _plot.enable_grouping and _plot.plot_grouping and getattr(_plot.plot_grouping, 'is_configured', False):
                        _min_reps = _plot.min_reps
                        _min_reps_ratio = _plot.min_reps_ratio
                        break

                minimize = self.comparison_processor._is_minimizing(objective)
                for group_label, group_data in grouped.items():
                    grouped_stats = self.extractor.extract_grouped_series_data(group_data['series_list'])
                    mean_values = grouped_stats.get('mean_values', [])
                    sample_counts = grouped_stats.get('sample_counts', [])

                    _threshold = compute_rep_threshold(_min_reps, _min_reps_ratio, sample_counts)
                    exp_trajectory = [
                        m for i, m in enumerate(mean_values)
                        if m is not None
                        and (i >= len(sample_counts) or sample_counts[i] is None or sample_counts[i] >= _threshold)
                    ]
                    if not exp_trajectory:
                        continue
                    runtimes = group_data['runtimes']
                    runtime = sum(runtimes) / len(runtimes) if runtimes else None
                    experiment_data = {
                        'name': group_label,
                        'display_name': group_label,
                        'trajectory': {objective: exp_trajectory},
                        'objective_values': {objective: exp_trajectory},
                        'runtime': runtime,
                        'timestamps': None,
                    }
                    matching = self._select_matching_baselines_from_meta(
                        group_data['meta'], group_label, baselines, cached_baseline_info
                    )
                    objective_comparisons.extend(
                        self._compare_against_baselines(experiment_data, group_label, objective, result_key, matching)
                    )
                if objective_comparisons:
                    comparisons[objective] = objective_comparisons
                continue

            for item in series_items:
                try:
                    experiment_data = {
                        'name': item.name,
                        'display_name': item.display_name,
                        'trajectory': {objective: item.series},
                        'objective_values': {objective: item.series},
                        'runtime': item.runtime,
                        'timestamps': item.time_series or None,
                    }
                    matching = self._select_matching_baselines_from_meta(
                        item.metadata, item.name, baselines, cached_baseline_info
                    )
                    objective_comparisons.extend(
                        self._compare_against_baselines(experiment_data, item.name, objective, result_key, matching)
                    )
                except Exception as e:
                    logger.error(f"Failed to process experiment: {e}")

            if objective_comparisons:
                comparisons[objective] = objective_comparisons

        return comparisons

    def _get_comparative_grouping_config(self) -> Optional[Any]:
        grouping = None
        for plot in self.config.plots:
            if plot.enable_grouping and plot.plot_grouping and plot.plot_grouping.is_configured:
                grouping = plot.plot_grouping
                break
        if grouping:
            logger.info("Comparative analysis grouping enabled using configured CustomGrouping")
        return grouping

    @staticmethod
    def _avg_runtime(experiments: List[Any], extractor: Any) -> Optional[float]:
        runtimes = [extractor.extract_runtime(exp) for exp in experiments]
        runtimes = [runtime for runtime in runtimes if runtime is not None]
        if not runtimes:
            return None
        return sum(runtimes) / len(runtimes)

    def _select_matching_baselines(self, exp: Any, exp_name: str, baselines: Dict[str, Any]) -> List[Any]:
        exp_meta = ExperimentMetadata.extract(exp)
        exp_task = self._normalize_key(exp_meta.get("task_name", ""))
        exp_display = self._normalize_key(self.parser.build_display_name(exp_name))
        exp_identifier = self._normalize_key(exp_name)

        matched = []
        for baseline_key, baseline in baselines.items():
            baseline_exp = getattr(baseline, 'raw_experiment', None)
            baseline_meta = ExperimentMetadata.extract(baseline_exp) if baseline_exp is not None else {}
            baseline_task = self._normalize_key(baseline_meta.get("task_name", ""))

            baseline_name = self._baseline_name(baseline_key, baseline)
            baseline_identifier = self._normalize_key(baseline_name)
            baseline_display = self._normalize_key(self.parser.build_display_name(baseline_name))

            if exp_task and baseline_task and exp_task == baseline_task:
                matched.append((baseline_key, baseline))
                continue

            if exp_identifier and baseline_identifier and exp_identifier == baseline_identifier:
                matched.append((baseline_key, baseline))
                continue

            if exp_display and baseline_display and exp_display == baseline_display:
                matched.append((baseline_key, baseline))

        if matched:
            return matched

        logger.warning(
            "No baseline matched experiment '%s' by task/id/display; using all selected baselines",
            exp_name,
        )
        return list(baselines.items())

    def _select_matching_baselines_from_meta(self, exp_meta: Dict[str, Any], exp_name: str,
                                             baselines: Dict[str, Any],
                                             cached_info: Optional[Dict[str, Any]] = None) -> List[Any]:
        exp_task = self._normalize_key(exp_meta.get("task_name", ""))
        exp_display = self._normalize_key(self.parser.build_display_name(exp_name))
        exp_identifier = self._normalize_key(exp_name)

        matched = []
        for baseline_key, baseline in baselines.items():
            if cached_info is not None and baseline_key in cached_info:
                info = cached_info[baseline_key]
                baseline_task = info['task']
                baseline_identifier = info['identifier']
                baseline_display = info['display']
            else:
                baseline_exp = getattr(baseline, 'raw_experiment', None)
                baseline_meta = ExperimentMetadata.extract(baseline_exp) if baseline_exp is not None else {}
                baseline_task = self._normalize_key(baseline_meta.get("task_name", ""))
                baseline_name = self._baseline_name(baseline_key, baseline)
                baseline_identifier = self._normalize_key(baseline_name)
                baseline_display = self._normalize_key(self.parser.build_display_name(baseline_name))

            if exp_task and baseline_task and exp_task == baseline_task:
                matched.append((baseline_key, baseline))
                continue

            if exp_identifier and baseline_identifier and exp_identifier == baseline_identifier:
                matched.append((baseline_key, baseline))
                continue

            if exp_display and baseline_display and exp_display == baseline_display:
                matched.append((baseline_key, baseline))

        if matched:
            return matched

        logger.warning(
            "No baseline matched experiment '%s' by task/id/display; using all selected baselines",
            exp_name,
        )
        return list(baselines.items())

    def _resolve_known_optimum(self, objective: str) -> Optional[float]:
        regret_config = self.config.comparative_analysis.regret_analysis
        if not regret_config:
            return None
        if regret_config.optimum_per_objective and objective in regret_config.optimum_per_objective:
            return regret_config.optimum_per_objective[objective]
        return regret_config.known_optimum

    def _compare_against_baselines(
        self,
        experiment_data: Dict[str, Any],
        exp_name: str,
        objective: str,
        result_key: str,
        matching_baselines: List[Any],
    ) -> List[Any]:
        """Run comparison against a pre-resolved list of (baseline_key, baseline) pairs."""
        results = []
        known_optimum = self._resolve_known_optimum(objective)
        for baseline_key, baseline in matching_baselines:
            try:
                result = self.comparison_processor.process_experiment_comparison(
                    experiment_data=experiment_data,
                    baseline=baseline,
                    objective=objective,
                    known_optimum=known_optimum,
                    result_key=result_key,
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Comparison failed for {exp_name} vs {baseline_key}: {e}")
        return results

    @staticmethod
    def _baseline_name(baseline_key: str, baseline: Any) -> str:
        raw_experiment = getattr(baseline, 'raw_experiment', None)
        if raw_experiment is None:
            return baseline_key
        return getattr(raw_experiment, 'name', None) or getattr(raw_experiment, 'ed_id', None) or baseline_key

    @staticmethod
    def _normalize_key(value: Any) -> str:
        if value is None:
            return ""
        text = str(value).strip().lower()
        if not text:
            return ""
        return re.sub(r'[^a-z0-9]+', '_', text).strip('_')
