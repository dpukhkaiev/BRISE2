import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class PlotType(Enum):
    CONVERGENCE = 'convergence_plot'
    CUSTOM = 'custom_plot'
    SCATTER = 'scatter_plot'


class MetricType(Enum):
    ITERATION = 'iteration'
    TIME = 'time'


class ScaleType(Enum):
    LINEAR = 'linear'
    LOG10 = 'log10'


class NormalizationType(Enum):
    MIN_OVER_ALL = 'min_over_all_experiments'
    MAX_OVER_ALL = 'max_over_all_experiments'
    NONE = 'none'


class OptimizationDirection(Enum):
    MINIMIZE = 'minimize'
    MAXIMIZE = 'maximize'


class Constants:
    DEFAULT_COLORS = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]


@dataclass
class AxisBounds:
    """Fixed axis limits for a single instance's scatter plot tab.

    All fields are optional — only the ones present override the auto-range.
    """
    x_min: Optional[float] = None
    x_max: Optional[float] = None
    y_min: Optional[float] = None
    y_max: Optional[float] = None


@dataclass
class PlotConfig:
    """Configuration for a single plot"""
    plot_type: str
    metric_description: str
    metric_label: str
    metric_scale: str
    metric_type: str
    objectives_to_plot: List[str]
    normalize: bool
    normalization_strategy: str
    objective_label: str
    objective_scale: str
    enable_grouping: bool = False
    # Per-plot overrides (all optional)
    title: Optional[str] = None
    filter_conditions: List[Any] = field(default_factory=list)   # List[MatchCondition]
    plot_grouping: Optional[Any] = None                           # Optional[CustomGroupingConfig]
    # Absolute minimum: iteration index is drawn only if this many reps contribute.
    # 1 = any sample shows (permissive). Higher values trim sparse tails.
    min_reps: int = 1
    # Relative minimum: fraction of the group's max rep count (0.0–1.0).
    # When set, overrides min_reps. E.g. 0.5 means at least 50% of reps must
    # contribute at an iteration for it to be drawn. Handles groups of
    # different sizes without needing to hard-code an absolute count.
    min_reps_ratio: Optional[float] = None
    # ScatterPlot only: 'metadata' (default, groups by experiment-level metadata)
    # or 'hyperparameter' (groups by per-iteration hyperparameter value, e.g. LLH selection).
    group_by: str = 'metadata'
    # ScatterPlot only: when False, draw a pure scatter (one full-opacity marker
    # trace per group, no aggregated mean line). True keeps the faint-dots +
    # bold-mean-line style. Set False to reproduce the old single-rep figures.
    scatter_show_mean_line: bool = True
    # Per-instance fixed axis limits for this scatter plot, keyed by the same
    # instance names as KnownOptima. Only axes with an explicit value override
    # the auto-range; others remain auto-ranged.
    known_axis_bounds: Dict[str, AxisBounds] = field(default_factory=dict)

    def uses_time_metric(self) -> bool:
        return self.metric_type == MetricType.TIME.value

    def should_plot_objective(self, objective: str) -> bool:
        return not self.objectives_to_plot or objective in self.objectives_to_plot


@dataclass
class TableConfig:
    """Configuration for table columns"""
    task: bool = True
    model: bool = True
    sampler: bool = True
    configuration_strategy: bool = True
    stop_condition: bool = True
    test_case: bool = False
    experiment: bool = True
    objective: bool = True
    iterations: bool = True
    initial_value: bool = True
    final_best_value: bool = True
    improvement_percentage: bool = True
    improvement_absolute: bool = True
    runtime: bool = True


@dataclass
class RegretAnalysisConfig:
    known_optimum: Optional[float] = None
    optimum_per_objective: Optional[Dict[str, float]] = None
    regret_type: List[str] = field(default_factory=lambda: ["iteration"])


@dataclass
class RelativeImprovementConfig:
    improvement_type: List[str] = field(default_factory=lambda: ["objective_value"])


@dataclass
class PerformanceProfileConfig:
    tau_max: float = 10.0
    tau_steps: int = 100
    objectives_to_profile: List[str] = field(default_factory=list)


@dataclass
class ComparativeTableConfig:
    experiment: bool = True
    baseline: bool = True
    relative_improvement: bool = True
    speedup_factor: bool = True
    converged_at_iteration: bool = True
    experiment_best: bool = True
    baseline_best: bool = True
    final_regret: bool = False


@dataclass
class ComparativeAnalysisConfig:
    show_summary_table: bool = True
    comparative_table: Optional[ComparativeTableConfig] = None
    regret_analysis: Optional[RegretAnalysisConfig] = None
    relative_improvement: Optional[RelativeImprovementConfig] = None
    performance_profile: Optional[PerformanceProfileConfig] = None

    def is_active(self) -> bool:
        return any([
            self.regret_analysis is not None,
            self.relative_improvement is not None,
            self.performance_profile is not None,
            self.comparative_table is not None
        ])

    def get_regret_types(self) -> List[str]:
        return self.regret_analysis.regret_type if self.regret_analysis else ["iteration"]

    def get_improvement_types(self) -> List[str]:
        return self.relative_improvement.improvement_type if self.relative_improvement else ["objective_value"]

    def get_tau_max(self) -> float:
        return self.performance_profile.tau_max if self.performance_profile else 10.0

    def get_tau_steps(self) -> int:
        return self.performance_profile.tau_steps if self.performance_profile else 100


@dataclass
class MatchCondition:
    """
    A single generic condition that checks one attribute of an experiment's metadata.

    ``path``     – dot-separated path into the experiment metadata dict produced by
                   ``ExperimentMetadata.extract()``, e.g. ``"problem_instance"`` or
                   ``"description.TaskConfiguration.Scenario.Hyperparameters"``.
    ``value``    – expected value (string equality / substring match when ``contains=True``).
    ``contains`` – if True, the extracted value is checked with ``value in extracted``
                   instead of strict equality.
    ``pattern``  – alternative to ``value``: a regex pattern matched against the extracted
                   string (takes precedence over ``value`` when set).
    """
    path: str
    value: Optional[str] = None
    contains: bool = False
    pattern: Optional[str] = None


@dataclass
class ValueGroupEntry:
    """Maps a concrete metadata value to a display label."""
    value: str
    display_name: str


@dataclass
class ValueGroupSpec:
    """Group experiments by a metadata path with explicit value-to-label mapping."""
    path: str
    groups: List[ValueGroupEntry] = field(default_factory=list)


@dataclass
class CustomGroupingConfig:
    """
    Groups experiments into legend lines by matching a metadata path to explicit display labels.

    ``value_groups`` maps specific metadata values at a given path to display labels.
    Experiments that don't match any entry fall back to their source filename.
    """
    value_groups: List[ValueGroupSpec] = field(default_factory=list)
    _value_lookup: Dict[str, Dict[str, str]] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        lookup: Dict[str, Dict[str, str]] = {}
        for spec in self.value_groups:
            if not spec.path:
                continue
            path_map = lookup.setdefault(spec.path, {})
            for entry in spec.groups:
                path_map[str(entry.value)] = str(entry.display_name)
        self._value_lookup = lookup

    @property
    def is_configured(self) -> bool:
        return bool(self.value_groups)

    @property
    def known_group_names(self) -> set:
        return {entry.display_name for spec in self.value_groups for entry in spec.groups}

    @property
    def ordered_group_names(self) -> List[str]:
        seen: set = set()
        result: List[str] = []
        for spec in self.value_groups:
            for entry in spec.groups:
                name = str(entry.display_name)
                if name not in seen:
                    seen.add(name)
                    result.append(name)
        return result


@dataclass
class BenchmarkConfig:
    """Main configuration for benchmark analysis"""
    results_folder: str
    output_directory: str
    experiment_name: str
    experiment_description: str
    objectives_to_measure: List[str]
    plots: List[PlotConfig]
    table_config: TableConfig
    comparative_analysis: ComparativeAnalysisConfig = field(default_factory=ComparativeAnalysisConfig)
    known_optima: Dict[str, float] = field(default_factory=dict)

    @staticmethod
    def _float_or_none(v: Any) -> Optional[float]:
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_metric_type(metric_description: str) -> str:
        return MetricType.TIME.value if 'time' in metric_description.lower() else MetricType.ITERATION.value

    @staticmethod
    def _parse_normalization_strategy(norm_strategy_data: Dict[str, Any]) -> str:
        if not isinstance(norm_strategy_data, dict):
            return NormalizationType.NONE.value

        if 'MinOverAll' in norm_strategy_data:
            return NormalizationType.MIN_OVER_ALL.value
        if 'MaxOverAll' in norm_strategy_data:
            return NormalizationType.MAX_OVER_ALL.value
        return NormalizationType.NONE.value

    @staticmethod
    def _create_plot_config(plot_type: str, plot_data: Dict[str, Any]) -> PlotConfig:
        objective_axis = plot_data.get("ObjectiveAxis", {})
        norm_strategy = BenchmarkConfig._parse_normalization_strategy(objective_axis.get("NormalizationStrategy", {}))

        filter_conditions = BenchmarkConfig._parse_match_conditions(
            plot_data.get("filterConditions", [])
        )

        # Per-plot grouping override (overrides global CustomGrouping for this plot)
        plot_grouping = None
        if "CustomGrouping" in plot_data:
            plot_grouping = BenchmarkConfig._parse_custom_grouping(plot_data.get("CustomGrouping", {}))

        is_box_plot = plot_type == "box_plot"
        if is_box_plot:
            if "MetricAxis" in plot_data:
                logger.warning("BoxPlot ignores MetricAxis because its x-axis is categorical (algorithm/test case groups)")
            metric_desc = "categorical groups"
            metric_label = "Algorithm"
            metric_scale = ScaleType.LINEAR.value
            metric_type = MetricType.ITERATION.value
        else:
            metric_axis = plot_data.get("MetricAxis", {})
            metric_desc = metric_axis.get("metricDescription", "iterations completed")
            metric_label = metric_axis.get("label", "iteration")
            metric_scale = metric_axis.get("scale", ScaleType.LINEAR.value)
            metric_type = BenchmarkConfig._parse_metric_type(metric_desc)

        try:
            min_reps = max(1, int(plot_data.get("minReps", 1)))
        except (TypeError, ValueError):
            min_reps = 1

        min_reps_ratio: Optional[float] = None
        raw_ratio = plot_data.get("minRepsRatio")
        if raw_ratio is not None:
            try:
                parsed = float(raw_ratio)
                if 0.0 < parsed <= 1.0:
                    min_reps_ratio = parsed
            except (TypeError, ValueError):
                pass

        raw_group_by = plot_data.get("groupBy", "metadata")
        group_by = raw_group_by if raw_group_by in ("metadata", "hyperparameter") else "metadata"

        scatter_show_mean_line = bool(plot_data.get("showMeanLine", True))

        # x bounds come from MetricAxis.KnownAxisBounds; y bounds from ObjectiveAxis.KnownAxisBounds.
        # Both are optional and independent — each is keyed by instance name.
        x_bounds: Dict[str, tuple] = {}
        raw_metric_bounds = plot_data.get("MetricAxis", {}).get("KnownAxisBounds", {})
        if isinstance(raw_metric_bounds, dict):
            for inst_key, val in raw_metric_bounds.items():
                if isinstance(val, dict):
                    x_bounds[inst_key] = (
                        BenchmarkConfig._float_or_none(val.get("xMin")),
                        BenchmarkConfig._float_or_none(val.get("xMax")),
                    )

        y_bounds: Dict[str, tuple] = {}
        raw_obj_bounds = plot_data.get("ObjectiveAxis", {}).get("KnownAxisBounds", {})
        if isinstance(raw_obj_bounds, dict):
            for inst_key, val in raw_obj_bounds.items():
                if isinstance(val, dict):
                    y_bounds[inst_key] = (
                        BenchmarkConfig._float_or_none(val.get("yMin")),
                        BenchmarkConfig._float_or_none(val.get("yMax")),
                    )

        known_axis_bounds: Dict[str, AxisBounds] = {}
        for inst_key in set(x_bounds) | set(y_bounds):
            x_min, x_max = x_bounds.get(inst_key, (None, None))
            y_min, y_max = y_bounds.get(inst_key, (None, None))
            known_axis_bounds[inst_key] = AxisBounds(
                x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max,
            )

        return PlotConfig(
            plot_type=plot_type,
            metric_description=metric_desc,
            metric_label=metric_label,
            metric_scale=metric_scale,
            metric_type=metric_type,
            objectives_to_plot=objective_axis.get("objectivesToPlot", []),
            normalize=objective_axis.get("normalize", True),
            normalization_strategy=norm_strategy,
            objective_label=objective_axis.get("label", "Objective value"),
            objective_scale=objective_axis.get("scale", ScaleType.LINEAR.value),
            enable_grouping=plot_data.get("enableGrouping", False),
            title=plot_data.get("title"),
            filter_conditions=filter_conditions,
            plot_grouping=plot_grouping,
            min_reps=min_reps,
            min_reps_ratio=min_reps_ratio,
            group_by=group_by,
            scatter_show_mean_line=scatter_show_mean_line,
            known_axis_bounds=known_axis_bounds,
        )

    @staticmethod
    def from_json(cfg: Dict[str, Any]) -> "BenchmarkConfig":
        benchmark = cfg.get("Benchmark", {})

        folder = benchmark.get("Resources", {}).get("Folder", "./results/serialized/")
        output_dir = benchmark.get("Report", {}).get("outputDirectory", "./results/reports/")

        experiment = benchmark.get("Experiment", {})

        table_dict = benchmark.get("Table", {})
        table_config = TableConfig(
            task=table_dict.get("task", True),
            model=table_dict.get("model", True),
            sampler=table_dict.get("sampler", True),
            configuration_strategy=table_dict.get("configurationStrategy", True),
            stop_condition=table_dict.get("stopCondition", True),
            experiment=table_dict.get("experiment", True),
            objective=table_dict.get("objective", True),
            iterations=table_dict.get("iterations", True),
            initial_value=table_dict.get("initialValue", True),
            final_best_value=table_dict.get("finalBestValue", True),
            improvement_percentage=table_dict.get("improvementPercentage", True),
            improvement_absolute=table_dict.get("improvementAbsolute", True),
            runtime=table_dict.get("runtime", True)
        )

        plots = []
        for plot_key in sorted(k for k in benchmark if k.startswith("Plot_")):
            plot_data = benchmark[plot_key]
            plot_type_data = plot_data.get("PlotType", {})

            if "ConvergencePlot" in plot_type_data:
                plots.append(BenchmarkConfig._create_plot_config(PlotType.CONVERGENCE.value, plot_type_data["ConvergencePlot"]))
            elif "CustomPlot" in plot_type_data:
                plots.append(BenchmarkConfig._create_plot_config(PlotType.CUSTOM.value, plot_type_data["CustomPlot"]))
            elif "BoxPlot" in plot_type_data:
                plots.append(BenchmarkConfig._create_plot_config("box_plot", plot_type_data["BoxPlot"]))
            elif "ScatterPlot" in plot_type_data:
                plots.append(BenchmarkConfig._create_plot_config(PlotType.SCATTER.value, plot_type_data["ScatterPlot"]))

        # Parse KnownOptima once; forward to RegretAnalysis.optimum_per_objective
        known_optima: Dict[str, float] = {}
        for key, val in benchmark.get("KnownOptima", {}).items():
            if isinstance(val, dict):
                # Waffle format: {"ObjectiveOptimum_N": {"objective": "kroA100.tsp", "optimum": 21282.0}}
                try:
                    known_optima[str(val["objective"])] = float(val["optimum"])
                except (KeyError, TypeError, ValueError):
                    pass
            else:
                # Manual format: {"kroA100.tsp": 21282}
                try:
                    known_optima[key] = float(val)
                except (TypeError, ValueError):
                    pass

        comparative_analysis = BenchmarkConfig._parse_comparative_analysis(
            benchmark.get("ComparativeAnalysis", {}),
            known_optima=known_optima,
        )

        return BenchmarkConfig(
            results_folder=folder,
            output_directory=output_dir,
            experiment_name=experiment.get("name", "BRISE Benchmark Report"),
            experiment_description=experiment.get("description", "Benchmark analysis results"),
            objectives_to_measure=experiment.get("objectivesToMeasure", []),
            plots=plots,
            table_config=table_config,
            comparative_analysis=comparative_analysis,
            known_optima=known_optima,
        )

    @staticmethod
    def _parse_custom_grouping(grouping_data: Dict[str, Any]) -> CustomGroupingConfig:
        """Parse a CustomGrouping block."""
        if not grouping_data:
            return None

        value_groups: List[ValueGroupSpec] = []

        if "valueGroups" in grouping_data:
            # Manual array format (hand-written configs):
            # {"valueGroups": [{"path": "...", "groups": [{"value": "...", "displayName": "..."}]}]}
            for spec in grouping_data.get("valueGroups", []) or []:
                if not isinstance(spec, dict):
                    continue
                path = spec.get("path", "")
                if not path:
                    continue
                entries: List[ValueGroupEntry] = []
                for entry in spec.get("groups", []) or []:
                    if not isinstance(entry, dict):
                        continue
                    value = entry.get("value")
                    display = entry.get("displayName") or entry.get("label")
                    if value is None or not display:
                        continue
                    entries.append(ValueGroupEntry(value=str(value), display_name=str(display)))
                if entries:
                    value_groups.append(ValueGroupSpec(path=path, groups=entries))
        else:
            # Waffle-generated structured format:
            # {"ValueGroupSpec_0": {"path": "...", "ValueGroupEntry_0": {"value": "...", "displayName": "..."}}}
            # Keys are sorted so that the configured display order is preserved.
            for spec_key in sorted(k for k in grouping_data if isinstance(grouping_data[k], dict) and "path" in grouping_data[k]):
                spec_val = grouping_data[spec_key]
                path = spec_val.get("path", "")
                if not path:
                    continue
                entries: List[ValueGroupEntry] = []
                for entry_key in sorted(k for k in spec_val if k != "path" and isinstance(spec_val[k], dict)):
                    entry_val = spec_val[entry_key]
                    value = entry_val.get("value")
                    display = entry_val.get("displayName") or entry_val.get("label")
                    if value is None or not display:
                        continue
                    entries.append(ValueGroupEntry(value=str(value), display_name=str(display)))
                if entries:
                    value_groups.append(ValueGroupSpec(path=path, groups=entries))

        if not value_groups:
            return None

        return CustomGroupingConfig(value_groups=value_groups)

    @staticmethod
    def _parse_match_conditions(conditions: Any) -> List[MatchCondition]:
        # Normalise to a flat list regardless of whether the source is the manual
        # array format or the Waffle-generated dict format.
        if isinstance(conditions, list):
            cond_list = conditions
        elif isinstance(conditions, dict):
            if "path" in conditions:
                # Waffle single-instance: the dict IS the one condition
                cond_list = [conditions]
            else:
                # Waffle multi-instance: {"filterConditions_0": {...}, ...}
                cond_list = [v for _, v in sorted(conditions.items()) if isinstance(v, dict)]
        else:
            return []

        parsed_conditions: List[MatchCondition] = []
        for cond in cond_list:
            if not isinstance(cond, dict):
                continue
            parsed_conditions.append(MatchCondition(
                path=cond.get("path", ""),
                value=cond.get("value"),
                contains=cond.get("contains", False),
                pattern=cond.get("pattern"),
            ))
        return parsed_conditions

    @staticmethod
    def _parse_comparative_analysis(comp_metrics_dict: Dict[str, Any],
                                    known_optima: Optional[Dict[str, float]] = None) -> ComparativeAnalysisConfig:
        if not comp_metrics_dict:
            # Still create a RegretAnalysisConfig if we have known_optima to forward
            if known_optima:
                return ComparativeAnalysisConfig(
                    regret_analysis=RegretAnalysisConfig(optimum_per_objective=known_optima)
                )
            return ComparativeAnalysisConfig()

        comp_table_dict = comp_metrics_dict.get("ComparativeTable", {})
        comp_table_config = ComparativeTableConfig(
            experiment=comp_table_dict.get("experiment", True),
            baseline=comp_table_dict.get("baseline", True),
            relative_improvement=comp_table_dict.get("relativeImprovement", True),
            speedup_factor=comp_table_dict.get("speedupFactor", comp_table_dict.get("speedup_factor", True)),
            converged_at_iteration=comp_table_dict.get("convergedAtIteration", True),
            experiment_best=comp_table_dict.get("experimentBest", True),
            baseline_best=comp_table_dict.get("baselineBest", True),
            final_regret=comp_table_dict.get("finalRegret", False)
        ) if comp_table_dict else None

        show_summary_table = comp_metrics_dict.get("showSummaryTable", comp_metrics_dict.get("show_summary_table", True))

        regret_dict = comp_metrics_dict.get("RegretAnalysis", {})
        if regret_dict:
            explicit_per_obj = regret_dict.get("optimumPerObjective")
            merged_per_obj = dict(known_optima or {})
            if explicit_per_obj:
                merged_per_obj.update(explicit_per_obj)
            regret_type_group = regret_dict.get("RegretType", {})
            if regret_type_group and isinstance(regret_type_group, dict):
                regret_type = [v["Type"] for v in regret_type_group.values() if isinstance(v, dict) and "Type" in v]
            else:
                regret_type = regret_dict.get("regretType", ["iteration"])
            regret_config = RegretAnalysisConfig(
                known_optimum=regret_dict.get("knownOptimum"),
                optimum_per_objective=merged_per_obj or None,
                regret_type=regret_type
            )
        elif known_optima:
            regret_config = RegretAnalysisConfig(optimum_per_objective=known_optima)
        else:
            regret_config = None

        relative_dict = comp_metrics_dict.get("RelativeImprovement", {})
        if relative_dict is not None:
            improvement_type_group = relative_dict.get("ImprovementType", {})
            if improvement_type_group and isinstance(improvement_type_group, dict):
                improvement_type = [v["Type"] for v in improvement_type_group.values() if isinstance(v, dict) and "Type" in v]
            else:
                improvement_type = relative_dict.get("improvementType", ["objective_value"])
            relative_config = RelativeImprovementConfig(improvement_type=improvement_type)
        else:
            relative_config = None

        performance_dict = comp_metrics_dict.get("PerformanceProfile", {})
        performance_config = PerformanceProfileConfig(
            tau_max=performance_dict.get("tauMax", 10.0),
            tau_steps=performance_dict.get("tauSteps", 100),
            objectives_to_profile=performance_dict.get("objectivesToProfile", [])
        ) if performance_dict else None

        return ComparativeAnalysisConfig(
            show_summary_table=show_summary_table,
            comparative_table=comp_table_config,
            regret_analysis=regret_config,
            relative_improvement=relative_config,
            performance_profile=performance_config
        )
