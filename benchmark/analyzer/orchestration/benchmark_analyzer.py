import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Any, Dict, Optional, Tuple, Set

import pandas as pd
import plotly.graph_objs as go

from analyzer.config import BenchmarkConfig, NormalizationType, PlotType
from analyzer.data_pipeline import ExperimentLoader, ExperimentParser, MetricExtractor, DataProcessor
from analyzer.data_pipeline.experiment_metadata import ExperimentMetadata
from analyzer.visualization import (PlotGenerator, TableGenerator, ReportGenerator)
from analyzer.visualization.comparative_plots import ComparativePlotGenerator
from analyzer.orchestration.comparative_orchestrator import ComparativeAnalysisOrchestrator
from analyzer.orchestration.analysis_services import (
    ObjectivePartitionService,
    ComparativeTableService,
    ExportService,
)
from analyzer.util.grouping_utils import build_group_label, matches_conditions

logger = logging.getLogger(__name__)


@dataclass
class ExperimentSeriesItem:
    name: str
    display_name: str
    source_filename: str
    metadata: Dict[str, Any]
    series: List[float]
    time_series: List[Optional[float]]
    runtime: Optional[float]
    raw_series: Optional[List[float]] = None
    llh_series: Optional[Dict[str, List[Optional[float]]]] = None


class BenchmarkAnalyzer:
    """Main analyzer orchestrator - delegates to appropriate pipelines based on configuration"""

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.loader = ExperimentLoader(config.results_folder)
        self.parser = ExperimentParser()
        self.extractor = MetricExtractor()
        self.processor = DataProcessor()
        self.plotter = PlotGenerator()
        self.table_gen = TableGenerator(self.parser, self.extractor)
        self.report_gen = ReportGenerator(config, self.table_gen)
        self.comparative_plotter = ComparativePlotGenerator()
        self.partition_service = ObjectivePartitionService(self.extractor)
        self.export_service = ExportService()

        self.comparative_orchestrator = None
        if self.config.comparative_analysis.is_active():
            logger.info("Initializing comparative analysis mode...")
            self.comparative_orchestrator = ComparativeAnalysisOrchestrator(config)

    def analyze(self, output_html: str, output_csv: str):
        """Main analysis entry point"""
        baselines = self.comparative_orchestrator.load_baseline_experiments() \
            if self.comparative_orchestrator else {}
        baseline_names = self._build_baseline_name_set(baselines)
        baseline_group_labels: Set[str] = set(baselines.keys()) if baselines else set()

        series_by_objective, tables_by_objective, result_keys = self._stream_experiment_items(
            baseline_names, baseline_group_labels
        )
        logger.info(f"Objectives: {list(series_by_objective.keys())}")

        objective_plots = self._generate_plots_from_series(series_by_objective, baselines, result_keys)

        comparative_results = {}
        comparative_plots = {}
        comparative_tables = {}
        performance_profile_plot = None

        if self.comparative_orchestrator and self.config.comparative_analysis.is_active():
            logger.info("Computing comparative metrics...")
            grouping_config = self.comparative_orchestrator._get_comparative_grouping_config()
            comparative_results = self.comparative_orchestrator.compute_comparative_metrics_streaming(
                series_by_objective, baselines, result_keys, grouping_config=grouping_config
            )
            if comparative_results:
                logger.info("Generating comparative plots...")
                comparative_plots = self._generate_comparative_plots(comparative_results)
                comparative_tables = self._build_comparative_tables(comparative_results)
                if self.config.comparative_analysis.performance_profile is not None:
                    logger.info("Computing global performance profile...")
                    performance_profile_plot = self._generate_global_performance_profile(comparative_results)

        del series_by_objective
        csv_files, comparative_csv_files, zip_file = self._save_csv_files(
            tables_by_objective,
            comparative_tables,
            output_csv,
        )
        self._generate_html_report(
            objective_plots=objective_plots,
            tables_by_objective=tables_by_objective,
            csv_files=csv_files,
            comparative_csv_files=comparative_csv_files,
            zip_file=zip_file,
            output_html=output_html,
            output_csv=output_csv,
            comparative_results=comparative_results,
            comparative_plots=comparative_plots,
            comparative_tables=comparative_tables,
            performance_profile_plot=performance_profile_plot,
        )

    def _stream_experiment_items(
        self,
        baseline_names: Set[str],
        baseline_group_labels: Set[str] = None,
        batch_size: int = 50,
    ) -> Tuple[Dict[str, List[ExperimentSeriesItem]], Dict[str, List[Dict[str, Any]]], Dict[str, str]]:
        objectives = list(self.config.objectives_to_measure or [])
        if not objectives:
            objectives = self._discover_objectives(batch_size)

        series_by_objective: Dict[str, List[ExperimentSeriesItem]] = {obj: [] for obj in objectives}
        tables_by_objective: Dict[str, List[Dict[str, Any]]] = {obj: [] for obj in objectives}
        result_keys: Dict[str, str] = {}

        needs_time = self._needs_time_series()
        needs_raw = self._needs_raw_series()
        needs_llh = self._needs_llh_series()
        llh_extraction_configs = self._get_llh_extraction_configs() if needs_llh else []

        # Resolve the grouping config once for label-based exclusion.
        _grouping_for_exclusion = None
        if baseline_group_labels:
            for plot in self.config.plots:
                if plot.enable_grouping and plot.plot_grouping and getattr(plot.plot_grouping, 'is_configured', False):
                    _grouping_for_exclusion = plot.plot_grouping
                    break

        batches = self.loader.iter_experiment_batches(batch_size)
        first_batch = next(batches, [])
        instance_mode = self._is_instance_mode(objectives, first_batch)

        def process_batch(batch: List[Any]) -> None:
            for exp in batch:
                exp_name = self.parser.get_name(exp)
                if exp_name in baseline_names:
                    continue

                meta = ExperimentMetadata.extract(exp)

                # Secondary gate: exclude by group label so that baseline
                # experiments whose .name is None/missing don't leak into
                # the main pool and produce a ghost solid baseline line.
                if baseline_group_labels and _grouping_for_exclusion is not None:
                    from analyzer.util.grouping_utils import build_group_label as _bgl
                    src = getattr(exp, '_source_filename', '')
                    lbl = _bgl(meta, exp_name, src, _grouping_for_exclusion)
                    if lbl in baseline_group_labels:
                        continue
                exp_objectives = self._objectives_for_experiment(meta, objectives, instance_mode)
                if not exp_objectives:
                    continue

                display_name = self.parser.build_display_name(exp_name)
                source_filename = getattr(exp, '_source_filename', '')
                runtime = self.extractor.extract_runtime(exp)

                for objective in exp_objectives:
                    result_key = result_keys.get(objective)
                    if result_key is None:
                        result_key = self._resolve_result_key_for_stream(objective, exp)
                        result_keys[objective] = result_key

                    series = self.extractor.extract_objective_series(exp, result_key)
                    if not series:
                        continue

                    row = self.table_gen.build_row(exp, objective, self.config.table_config)
                    if row:
                        tables_by_objective.setdefault(objective, []).append(row)

                    time_series = self.extractor.extract_time_series(exp) if needs_time else []
                    raw_series = self.extractor.extract_raw_objective_series(exp, result_key) if needs_raw else None
                    llh_series = None
                    if llh_extraction_configs:
                        llh_series = {}
                        for llh_path, name_mapping in llh_extraction_configs:
                            llh_series.update(
                                self.extractor.extract_llh_series(exp, result_key, llh_path, name_mapping)
                            )
                    series_by_objective.setdefault(objective, []).append(ExperimentSeriesItem(
                        name=exp_name,
                        display_name=display_name,
                        source_filename=source_filename,
                        metadata=meta,
                        series=series,
                        time_series=time_series,
                        runtime=runtime,
                        raw_series=raw_series,
                        llh_series=llh_series,
                    ))

        if first_batch:
            process_batch(first_batch)
        for batch in batches:
            process_batch(batch)

        series_by_objective = {k: v for k, v in series_by_objective.items() if v}
        tables_by_objective = {k: v for k, v in tables_by_objective.items() if v}
        return series_by_objective, tables_by_objective, result_keys

    def _discover_objectives(self, batch_size: int) -> List[str]:
        discovered: Set[str] = set()
        for batch in self.loader.iter_experiment_batches(batch_size):
            discovered.update(self.extractor.discover_objectives(batch))
        result = sorted(discovered)
        if result:
            logger.info(f"Discovered result keys: {result}")
        return result

    @staticmethod
    def _is_instance_mode(objectives: List[str], experiments: List[Any]) -> bool:
        if not objectives or not experiments:
            return False
        sample_instances = {
            ExperimentMetadata.extract(exp).get("problem_instance", "")
            for exp in experiments
        }
        return any(obj in sample_instances for obj in objectives)

    @staticmethod
    def _objectives_for_experiment(meta: Dict[str, Any], objectives: List[str], instance_mode: bool) -> List[str]:
        if not objectives:
            return []
        if not instance_mode:
            return objectives
        instance = meta.get("problem_instance", "")
        return [instance] if instance in objectives else []

    @staticmethod
    def _resolve_result_key_for_stream(objective: str, exp: Any) -> str:
        sample_configs = getattr(exp, 'measured_configurations', [])[:1]
        if sample_configs:
            keys = set(getattr(sample_configs[0], 'results', {}).keys())
            if objective not in keys and 'objective' in keys:
                return 'objective'
        return objective

    def _needs_time_series(self) -> bool:
        if any(plot.uses_time_metric() for plot in self.config.plots):
            return True
        if self.config.comparative_analysis and self.config.comparative_analysis.regret_analysis:
            return "time" in self.config.comparative_analysis.regret_analysis.regret_type
        return False

    def _needs_raw_series(self) -> bool:
        return any(
            plot.plot_type == PlotType.SCATTER.value and plot.group_by == 'metadata'
            for plot in self.config.plots
        )

    def _needs_llh_series(self) -> bool:
        return any(
            plot.plot_type == PlotType.SCATTER.value and plot.group_by == 'hyperparameter'
            for plot in self.config.plots
        )

    def _get_llh_extraction_configs(self) -> List[Tuple[str, Dict[str, str]]]:
        """Return [(llh_path, name_mapping), ...] for all hyperparameter-grouped scatter plots."""
        seen: set = set()
        results: List[Tuple[str, Dict[str, str]]] = []
        for plot in self.config.plots:
            if plot.plot_type != PlotType.SCATTER.value or plot.group_by != 'hyperparameter':
                continue
            grouping = plot.plot_grouping
            if not (grouping and getattr(grouping, 'is_configured', False)):
                continue
            for spec in grouping.value_groups:
                key = spec.path
                if key in seen:
                    continue
                seen.add(key)
                name_mapping = {entry.value: entry.display_name for entry in spec.groups}
                results.append((key, name_mapping))
        return results

    @staticmethod
    def _build_baseline_name_set(baselines: Dict[str, Any]) -> Set[str]:
        baseline_names = set()
        for bl in baselines.values():
            raw_exp = getattr(bl, 'raw_experiment', None)
            if raw_exp is not None:
                baseline_names.add(getattr(raw_exp, 'name', None) or getattr(raw_exp, 'ed_id', None))
            raw_group = getattr(bl, 'raw_experiments', None) or []
            for exp in raw_group:
                baseline_names.add(getattr(exp, 'name', None) or getattr(exp, 'ed_id', None))
        return {name for name in baseline_names if name}

    def _generate_plots_from_series(
        self,
        series_by_objective: Dict[str, List[ExperimentSeriesItem]],
        baselines: Dict[str, Any],
        result_keys: Dict[str, str],
    ) -> Dict[str, List[go.Figure]]:
        objective_plots: Dict[str, List[go.Figure]] = {}

        for objective, items in series_by_objective.items():
            obj_baselines = self._filter_baselines_for_objective(baselines, objective)
            result_key = result_keys.get(objective, objective)
            figures = self._make_figures_from_series(result_key, items, obj_baselines, objective)
            if figures:
                objective_plots[objective] = figures

        return objective_plots

    def _make_figures_from_series(
        self,
        result_key: str,
        items: List[ExperimentSeriesItem],
        baselines: Dict[str, Any],
        partition_key: str = "",
    ) -> List[go.Figure]:
        known_optimum = self.config.known_optima.get(partition_key) if partition_key else None

        figures = []
        for plot_config in self.config.plots:
            if not plot_config.should_plot_objective(result_key):
                continue

            conditions = plot_config.filter_conditions or []
            plot_items = [
                item for item in items
                if matches_conditions(item.metadata, conditions)
            ]
            grouping = plot_config.plot_grouping
            title_suffix = self._build_plot_title_suffix(plot_config)

            if plot_config.enable_grouping:
                is_scatter = plot_config.plot_type == PlotType.SCATTER.value
                if is_scatter and plot_config.group_by == 'hyperparameter':
                    groups = self._build_llh_groups(plot_items, grouping)
                else:
                    groups = self._build_series_groups(plot_items, grouping, use_raw=is_scatter)
                logger.info(
                    f"  [{partition_key or result_key}] plot '{title_suffix or 'default'}': "
                    f"{len(plot_items)} experiments -> {len(groups)} groups"
                )
                if is_scatter:
                    axis_bounds = plot_config.known_axis_bounds.get(partition_key) if partition_key else None
                    fig = self.plotter.create_scatter_plot_from_series(
                        result_key,
                        groups,
                        plot_config,
                        title_suffix=title_suffix,
                        known_optimum=known_optimum,
                        show_mean_line=plot_config.scatter_show_mean_line,
                        axis_bounds=axis_bounds,
                    )
                else:
                    fig = self.plotter.create_grouped_plot_from_series(
                        result_key,
                        groups,
                        plot_config,
                        self.extractor,
                        baselines,
                        title_suffix=title_suffix,
                        known_optimum=known_optimum,
                        objective_instance=partition_key or None,
                    )
            else:
                fig = self._create_plot_from_series(
                    plot_items,
                    result_key,
                    plot_config,
                    baselines,
                    known_optimum=known_optimum,
                    title_suffix=title_suffix,
                    objective_instance=partition_key or None,
                )
            if fig:
                figures.append(fig)
        return figures

    def _build_series_groups(self, items: List[ExperimentSeriesItem], grouping, use_raw: bool = False) -> Dict[str, Dict[str, Any]]:
        known = grouping.known_group_names if (grouping and getattr(grouping, 'is_configured', False)) else None
        groups: Dict[str, Dict[str, Any]] = {}
        for item in items:
            label = build_group_label(item.metadata, item.name, item.source_filename, grouping)
            if known is not None and label not in known:
                continue
            group = groups.setdefault(label, {'series_list': [], 'time_series_list': [], 'final_values': []})
            series_to_use = (item.raw_series if (use_raw and item.raw_series) else item.series)
            group['series_list'].append(series_to_use)
            if item.time_series:
                group['time_series_list'].append(item.time_series)
            if item.series:
                final_val = item.series[-1]
                if final_val is not None:
                    try:
                        if math.isfinite(final_val):
                            group['final_values'].append(final_val)
                    except Exception:
                        group['final_values'].append(final_val)
        if grouping and getattr(grouping, 'is_configured', False):
            ordered = grouping.ordered_group_names
            groups = {k: groups[k] for k in ordered if k in groups}
        return groups

    def _build_llh_groups(
        self,
        items: List[ExperimentSeriesItem],
        grouping,
    ) -> Dict[str, Dict[str, Any]]:
        """Build series groups keyed by per-iteration LLH selection.

        Each item's ``llh_series`` dict maps display names to a sparse series
        (None where that LLH was not selected). Groups aggregate those sparse
        series across all repetitions (items).
        """
        ordered_names = grouping.ordered_group_names if (grouping and getattr(grouping, 'is_configured', False)) else []
        groups: Dict[str, Dict[str, Any]] = {name: {'series_list': [], 'time_series_list': [], 'final_values': []} for name in ordered_names}

        for item in items:
            if not item.llh_series:
                continue
            for llh_name, sparse_series in item.llh_series.items():
                if llh_name not in groups:
                    continue
                groups[llh_name]['series_list'].append(sparse_series)

        # Drop groups with no data
        groups = {k: v for k, v in groups.items() if v['series_list']}
        return groups

    def _create_plot_from_series(
        self,
        items: List[ExperimentSeriesItem],
        objective: str,
        plot_config: Any,
        baselines: Dict[str, Any] = None,
        known_optimum: Optional[float] = None,
        title_suffix: str = "",
        objective_instance: Optional[str] = None,
    ) -> Optional[go.Figure]:
        names = [item.display_name for item in items]
        data_series = [item.series for item in items]
        time_series = [item.time_series for item in items] if plot_config.uses_time_metric() else []

        if not data_series:
            return None

        normalized_baselines = baselines
        if plot_config.normalize and baselines:
            data_series, normalized_baselines = self._normalize_with_baselines(
                data_series, baselines, objective, plot_config.normalization_strategy,
                objective_instance=objective_instance
            )
        elif plot_config.normalize:
            data_series = self.processor.normalize_series(data_series, plot_config.normalization_strategy)

        if plot_config.plot_type == 'box_plot':
            return self.plotter.create_box_plot(
                objective,
                names,
                data_series,
                plot_config,
                normalized_baselines,
                known_optimum=known_optimum,
                objective_instance=objective_instance,
            )
        if plot_config.uses_time_metric():
            return self.plotter.create_custom_plot(
                objective,
                names,
                data_series,
                time_series,
                plot_config,
                normalized_baselines,
                known_optimum=known_optimum,
                objective_instance=objective_instance,
            )
        return self.plotter.create_convergence_plot(
            objective,
            names,
            data_series,
            plot_config,
            normalized_baselines,
            known_optimum=known_optimum,
            title_suffix=title_suffix,
            objective_instance=objective_instance,
        )

    @staticmethod
    def _build_plot_title_suffix(plot_config) -> str:
        """Build a suffix from filter conditions (used when no explicit title is set)."""
        if plot_config.title:
            return ""
        if plot_config.filter_conditions:
            parts = [
                f"{c.path.split('.')[-1]}={c.value}"
                for c in plot_config.filter_conditions if c.value
            ]
            return f" [{', '.join(parts)}]" if parts else ""
        return ""


    def _filter_baselines_for_objective(self, baselines: Dict[str, Any], objective: str) -> Dict[str, Any]:
        """Filter baselines to only those relevant for the current objective"""
        filtered = {}
        for baseline_key, baseline_result in baselines.items():
            # Check if this baseline's objectives include the current one
            if hasattr(baseline_result, 'metadata') and baseline_result.metadata:
                if objective in baseline_result.metadata.objectives:
                    filtered[baseline_key] = baseline_result
            # Also include if we can't check (be permissive)
            elif baseline_result:
                filtered[baseline_key] = baseline_result
        return filtered

    def _generate_comparative_plots(self, comparative_results: Dict[str, List[Any]]) -> Dict[str, List[go.Figure]]:
        """Generate comparative analysis plots from comparison results."""
        comparative_plots = {}

        for objective, comparison_list in comparative_results.items():
            if not comparison_list:
                continue

            plots = []
            regret_type_labels = {"iteration": "Regret Analysis (Iterations)", "time": "Regret Analysis (Time)"}
            improvement_type_labels = {
                "objective_value": ("Relative Improvement", "Objective Value"),
                "time_to_target": ("Relative Improvement: Speedup Factor", "Time"),
                "iteration_to_target": ("Relative Improvement: Speedup Factor", "Iterations")
            }

            for regret_type in self.config.comparative_analysis.get_regret_types():
                fig = self.comparative_plotter.plot_regret_curves(
                    comparison_list,
                    title=f"{objective} - {regret_type_labels.get(regret_type, 'Regret Analysis')}",
                    regret_type=regret_type
                )
                if fig:
                    plots.append(fig)

            for imp_type in self.config.comparative_analysis.get_improvement_types():
                metric_type, dimension = improvement_type_labels.get(imp_type, ("Relative Improvement", imp_type))
                fig = self.comparative_plotter.plot_relative_improvement(
                    comparison_list,
                    title=f"{objective} - {metric_type} ({dimension})",
                    improvement_type=imp_type
                )
                if fig:
                    plots.append(fig)

            if plots:
                comparative_plots[objective] = plots

        return comparative_plots

    def _generate_global_performance_profile(self, comparative_results: Dict[str, List[Any]]) -> Optional[go.Figure]:
        """
        Generate global performance profile comparing test cases across all objectives.

        Each test case (test_case_0, test_case_2, test_case_9, random-search, grid-search)
        is treated as an "algorithm" and compared across multiple "problems" (objectives).

        Returns:
            Performance profile figure, or None if not enough data
        """
        from analyzer.comparison.comparative_metrics import PerformanceProfileCalculator

        test_case_performance = {}
        baseline_performance = {}

        for objective, comparison_list in comparative_results.items():
            for result in comparison_list:
                if not result.experiment_trajectory:
                    continue

                test_case_name = result.display_name or result.experiment_name
                best_exp_value = min(result.experiment_trajectory)

                test_case_performance.setdefault(test_case_name, {})
                test_case_performance[test_case_name].setdefault(objective, best_exp_value)

                if result.baseline_trajectory and result.baseline_type:
                    baseline_name = self.parser.build_display_name(result.baseline_type)
                    baseline_performance.setdefault(baseline_name, {})
                    baseline_performance[baseline_name].setdefault(objective, min(result.baseline_trajectory))

        for baseline_name, perf_data in baseline_performance.items():
            test_case_performance.setdefault(baseline_name, perf_data)

        if len(test_case_performance) < 2:
            logger.warning(f"Performance profile: Need at least 2 test cases (have {len(test_case_performance)})")
            return None

        objectives = sorted({obj for tc_data in test_case_performance.values() for obj in tc_data})

        if self.config.comparative_analysis.performance_profile and self.config.comparative_analysis.performance_profile.objectives_to_profile:
            configured = self.config.comparative_analysis.performance_profile.objectives_to_profile
            objectives = [obj for obj in objectives if obj in configured]

        if len(objectives) < 2:
            logger.warning(f"Performance profile: Need at least 2 objectives (have {len(objectives)})")
            return None

        df = pd.DataFrame(
            [{tc: test_case_performance[tc].get(obj) for tc in test_case_performance} for obj in objectives],
            index=objectives
        )

        df_complete = df.dropna(axis=1)
        excluded = [col for col in df.columns if col not in df_complete.columns]
        if excluded:
            logger.info(f"Excluded test cases with incomplete data: {excluded}")

        if len(df_complete.columns) < 2:
            logger.warning(f"Performance profile: Need at least 2 complete test cases (have {len(df_complete.columns)})")
            return None

        logger.info(f"Performance profile: {len(df_complete.columns)} test cases × {len(df_complete)} objectives")

        calculator = PerformanceProfileCalculator()
        try:
            algo_dict = {col: df_complete[col].tolist() for col in df_complete.columns}
            ratios_df = calculator.calculate_performance_ratios(algo_dict, minimize=True)

            performance_profiles = calculator.generate_performance_profile(
                ratios_df,
                tau_range=(1.0, self.config.comparative_analysis.get_tau_max()),
                tau_steps=self.config.comparative_analysis.get_tau_steps()
            )

            if not performance_profiles:
                return None

            objectives_str = ", ".join(objectives)
            return self.comparative_plotter.plot_performance_profile(
                performance_profiles,
                title=f"Performance Profile - Test Case Comparison Across {{{objectives_str}}}"
            )
        except Exception as e:
            logger.error(f"Failed to generate global performance profile: {e}", exc_info=True)
            return None

    def _normalize_with_baselines(
        self,
        data_series: List[List[float]],
        baselines: Dict[str, Any],
        objective: str,
        normalization_strategy: str,
        objective_instance: Optional[str] = None,
    ) -> Tuple[List[List[float]], Dict[str, Any]]:
        """
        Normalize experiments and baselines together using the same normalization factor.

        This ensures baselines and experiments are on the same scale when plotted.
        """
        from analyzer.comparison.comparison_processor import ComparisonProcessor
        from analyzer.comparison.baseline_manager import BaselineResult

        if normalization_strategy == NormalizationType.NONE.value:
            return data_series, baselines

        cache_key = objective_instance or objective
        # Extract each baseline trajectory once and cache by key to avoid double extraction
        baseline_trajs = {
            k: t
            for k, bl in baselines.items()
            for t in [ComparisonProcessor._extract_baseline_trajectory(bl, cache_key, minimize=True, result_key=objective)]
            if t
        }

        all_series = data_series + list(baseline_trajs.values())

        if normalization_strategy == NormalizationType.MIN_OVER_ALL.value:
            all_mins = [min((y for y in s if y is not None), default=None) for s in all_series]
            global_min = min((m for m in all_mins if m is not None), default=None)

            if global_min is None or global_min == 0:
                return data_series, baselines

            normalized_experiments = [[(y / global_min) if y is not None else None for y in s] for s in data_series]

            normalized_baselines = {}
            for baseline_key, baseline_result in baselines.items():
                traj = baseline_trajs.get(baseline_key)
                if traj:
                    normalized_traj = [(y / global_min) if y is not None else None for y in traj]
                    normalized_baselines[baseline_key] = BaselineResult(
                        baseline_id=baseline_result.baseline_id,
                        baseline_type=baseline_result.baseline_type,
                        trajectory=normalized_traj,
                        best_value=min((v for v in normalized_traj if v is not None), default=float('inf')),
                        raw_experiment=baseline_result.raw_experiment
                    )
                else:
                    normalized_baselines[baseline_key] = baseline_result

            return normalized_experiments, normalized_baselines

        if normalization_strategy == NormalizationType.MAX_OVER_ALL.value:
            all_maxes = [max((y for y in s if y is not None), default=None) for s in all_series]
            global_max = max((m for m in all_maxes if m is not None), default=None)

            if global_max is None or global_max == 0:
                return data_series, baselines

            normalized_experiments = [[(y / global_max) if y is not None else None for y in s] for s in data_series]

            normalized_baselines = {}
            for baseline_key, baseline_result in baselines.items():
                traj = baseline_trajs.get(baseline_key)
                if traj:
                    normalized_traj = [(y / global_max) if y is not None else None for y in traj]
                    normalized_baselines[baseline_key] = BaselineResult(
                        baseline_id=baseline_result.baseline_id,
                        baseline_type=baseline_result.baseline_type,
                        trajectory=normalized_traj,
                        best_value=max((v for v in normalized_traj if v is not None), default=float('-inf')),
                        raw_experiment=baseline_result.raw_experiment
                    )
                else:
                    normalized_baselines[baseline_key] = baseline_result

            return normalized_experiments, normalized_baselines

        return data_series, baselines


    def _build_comparative_tables(self, comparative_results: Dict[str, List[Any]]) -> Dict[str, List[Dict[str, Any]]]:
        table_config = self.config.comparative_analysis.comparative_table
        is_minimizing_fn = None
        if self.comparative_orchestrator:
            is_minimizing_fn = self.comparative_orchestrator.comparison_processor._is_minimizing
        return ComparativeTableService.build(comparative_results, table_config, is_minimizing_fn)

    def _save_csv_files(
        self,
        tables_by_objective: Dict[str, List[Dict[str, Any]]],
        comparative_tables: Dict[str, List[Dict[str, Any]]],
        output_csv: str,
    ) -> Tuple[Dict[str, str], Dict[str, str], Optional[str]]:
        return self.export_service.save_csv_files(tables_by_objective, output_csv, comparative_tables)

    def _generate_html_report(self, objective_plots, tables_by_objective, csv_files, comparative_csv_files, zip_file,
                              output_html, output_csv, comparative_results=None,
                              comparative_plots=None, comparative_tables=None,
                              performance_profile_plot=None):
        logger.info("Generating HTML report...")
        html_content = self.report_gen.generate(
            objective_plots, tables_by_objective, csv_files, zip_file,
            comparative_plots, comparative_tables or {}, performance_profile_plot,
            comparative_csv_files=comparative_csv_files,
        )
        html_path = Path(output_html)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(html_content, encoding='utf-8')

        logger.info(f"Report generated: {html_path}")
        logger.info(f"CSV (combined): {output_csv}")
        if comparative_results:
            num_comparisons = sum(len(v) for v in comparative_results.values())
            logger.info(f"Comparative analysis completed with {num_comparisons} comparison(s)")
        logger.info("Analysis complete!")
