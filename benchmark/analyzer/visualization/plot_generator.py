from collections import OrderedDict
from typing import List, Optional, Dict, Any, Tuple

import numpy as np
import plotly.graph_objs as go

from analyzer.config import Constants, ScaleType
from analyzer.config.benchmark_config import PlotConfig
from analyzer.data_pipeline import ExperimentParser
from analyzer.util.grouping_utils import compute_rep_threshold
from analyzer.util.trajectory_utils import extract_baseline_trajectory, extract_best_so_far_series


_LEGEND_STYLE = dict(
    font=dict(size=13),
    bgcolor='rgba(255, 255, 255, 0.75)',
    bordercolor='rgba(0, 0, 0, 0.12)',
    borderwidth=1,
)


class PlotGenerator:
    """Generates Plotly figures for benchmark results"""

    def __init__(self):
        self.parser = ExperimentParser()

    @staticmethod
    def _build_plot_title(objective: str, plot_config: PlotConfig, title_suffix: str = "") -> str:
        if plot_config.title is not None:
            return plot_config.title
        return f"{objective}{title_suffix}"

    @staticmethod
    def _compute_robust_y_range(values: List[float], padding_ratio: float = 0.05) -> Optional[List[float]]:
        finite_vals = np.array([v for v in values if v is not None and np.isfinite(v)])
        if finite_vals.size == 0:
            return None
        min_y, max_y = float(np.min(finite_vals)), float(np.max(finite_vals))
        if not np.isfinite(min_y) or not np.isfinite(max_y):
            return None
        pad = padding_ratio * (max_y - min_y) if max_y != min_y else padding_ratio * (abs(min_y) if min_y != 0 else 1.0)
        return [min_y - pad, max_y + pad]


    @staticmethod
    def _hex_to_rgba(hex_color: str, alpha: float = 0.2) -> str:
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f'rgba({r}, {g}, {b}, {alpha})'

    @staticmethod
    def _create_scatter_trace(x_vals: List[Any], y_vals: List[Any], name: str, single_point: bool = False) -> go.Scatter:
        mode = 'markers' if single_point else 'lines+markers'
        trace = go.Scatter(x=x_vals, y=y_vals, mode=mode, name=name)
        if single_point:
            trace.update(marker=dict(size=12))
        return trace

    @staticmethod
    def _apply_axis_config(layout: Dict[str, Any], plot_config: PlotConfig):
        if plot_config.metric_scale == ScaleType.LOG10.value:
            layout['xaxis']['type'] = 'log'
        if plot_config.objective_scale == ScaleType.LOG10.value:
            layout['yaxis']['type'] = 'log'

    @staticmethod
    def _apply_axis_bounds(layout: Dict[str, Any], axis_bounds: Optional[Any], fallback_values: List[float]) -> None:
        """Apply axis ranges from ``axis_bounds`` (an ``AxisBounds`` instance).

        For each axis, if an explicit bound is present it takes precedence over the
        auto-computed range; otherwise the fallback auto-range is used.  Mixing is
        supported: e.g. ``x_max`` fixed, ``y_min``/``y_max`` auto.
        """
        # --- x axis ---
        x_min_explicit = getattr(axis_bounds, 'x_min', None) if axis_bounds else None
        x_max_explicit = getattr(axis_bounds, 'x_max', None) if axis_bounds else None
        if x_min_explicit is not None or x_max_explicit is not None:
            x_min = x_min_explicit if x_min_explicit is not None else 0
            x_max = x_max_explicit  # None means Plotly auto-range on the upper side (rare)
            layout['xaxis']['range'] = [x_min, x_max]

        # --- y axis ---
        y_min_explicit = getattr(axis_bounds, 'y_min', None) if axis_bounds else None
        y_max_explicit = getattr(axis_bounds, 'y_max', None) if axis_bounds else None
        if y_min_explicit is not None or y_max_explicit is not None:
            y_min = y_min_explicit if y_min_explicit is not None else 0
            y_max = y_max_explicit if y_max_explicit is not None else (
                max(fallback_values) * 1.05 if fallback_values else None
            )
            layout['yaxis']['range'] = [y_min, y_max]
        else:
            # Fall back to auto-range from data
            y_range = PlotGenerator._compute_robust_y_range(fallback_values)
            if y_range:
                layout['yaxis']['range'] = y_range

    @staticmethod
    def _optimum_trace(known_optimum: float) -> go.Scatter:
        """Invisible scatter used to add a green dashed optimum line to the legend."""
        return go.Scatter(
            x=[None], y=[None], mode='lines',
            line=dict(color='green', dash='dash', width=1.5),
            name=f'Optimum ({known_optimum:g})',
        )

    @staticmethod
    def _optimum_shape(known_optimum: float) -> Dict[str, Any]:
        """Plotly shape dict for a horizontal dashed green reference line."""
        return dict(
            type='line', xref='paper', x0=0, x1=1,
            yref='y', y0=known_optimum, y1=known_optimum,
            line=dict(color='green', dash='dash', width=1.5),
        )

    @staticmethod
    def _add_optimum_to_layout(layout: Dict[str, Any], known_optimum: float):
        layout.setdefault('shapes', [])
        layout['shapes'].append(PlotGenerator._optimum_shape(known_optimum))

    def _create_baseline_traces(
        self,
        baselines: Dict[str, Any],
        objective: str,
        objective_instance: Optional[str] = None,
    ) -> Tuple[List[go.Scatter], List[float]]:
        """Create baseline traces showing best-so-far values per iteration."""
        traces = []
        all_values = []
        baseline_colors = ['#888888', '#2d2d2d', '#d62728', '#ff7f0e', '#9467bd']
        baseline_dashes = ['dash', 'dot', 'dashdot']

        for idx, (baseline_key, baseline_result) in enumerate(baselines.items()):
            color = baseline_colors[idx % len(baseline_colors)]
            dash = baseline_dashes[idx % len(baseline_dashes)]
            display_name = self.parser.build_display_name(baseline_key)
            cache_key = objective_instance or objective

            trajectory = extract_baseline_trajectory(
                baseline_result,
                cache_key,
                prefer_cached=True,
                best_so_far_fallback=True,
                minimize=True,
                result_key=objective,
            )

            if trajectory:
                x_vals = list(range(len(trajectory)))
                all_values.extend([v for v in trajectory if v is not None and np.isfinite(v)])
                traces.append(go.Scatter(
                    x=x_vals, y=trajectory, mode='lines', name=display_name,
                    line=dict(color=color, dash=dash, width=2.5),
                    hovertemplate='%{x}, %{y:.4f}<extra></extra>'
                ))

        return traces, all_values

    def create_convergence_plot(self, objective: str, experiment_names: List[str], data_series: List[List[float]],
            plot_config: PlotConfig, baselines: Dict[str, Any] = None,
            known_optimum: Optional[float] = None,
            title_suffix: str = "",
            objective_instance: Optional[str] = None) -> go.Figure:
        """Plot best-so-far objective values per iteration with optional known-optimum reference."""
        traces = []
        all_values = []
        max_iterations = 0

        for series, name in zip(data_series, experiment_names):
            x_vals = list(range(len(series)))
            max_iterations = max(max_iterations, len(series))
            all_values.extend([v for v in series if v is not None])
            traces.append(self._create_scatter_trace(x_vals, series, name, len(series) <= 1))

        if baselines:
            baseline_traces, baseline_values = self._create_baseline_traces(baselines, objective, objective_instance=objective_instance)
            traces.extend(baseline_traces)
            all_values.extend(baseline_values)
            for baseline_result in baselines.values():
                if hasattr(baseline_result, 'trajectory'):
                    max_iterations = max(max_iterations, len(baseline_result.trajectory))

        layout = dict(
            title=self._build_plot_title(objective, plot_config, title_suffix),
            xaxis=dict(title=plot_config.metric_label,
                       range=[-0.5, max_iterations - 0.5 if max_iterations > 1 else 0.5]),
            yaxis=dict(title=plot_config.objective_label),
            legend=_LEGEND_STYLE,
        )
        y_range = self._compute_robust_y_range(all_values)
        if y_range:
            layout['yaxis']['range'] = y_range
        if known_optimum is not None:
            self._add_optimum_to_layout(layout, known_optimum)
            traces.append(self._optimum_trace(known_optimum))

        self._apply_axis_config(layout, plot_config)
        return go.Figure(data=traces, layout=layout)

    def create_custom_plot(self, objective: str, experiment_names: List[str], objective_series: List[List[float]],
            time_series: List[List[Optional[float]]], plot_config: PlotConfig,
            baselines: Dict[str, Any] = None,
            known_optimum: Optional[float] = None,
            objective_instance: Optional[str] = None) -> Optional[go.Figure]:
        traces = []
        all_objective = []

        for obj_vals, time_vals, name in zip(objective_series, time_series, experiment_names):
            valid_pairs = [(time_vals[i], obj_vals[i]) for i in range(min(len(obj_vals), len(time_vals)))
                           if obj_vals[i] is not None and time_vals[i] is not None]
            if not valid_pairs:
                continue
            x_vals, y_vals = zip(*valid_pairs)
            all_objective.extend(y_vals)
            traces.append(self._create_scatter_trace(x_vals, y_vals, name, len(valid_pairs) <= 1))

        if baselines:
            baseline_traces, baseline_values = self._create_baseline_traces(baselines, objective, objective_instance=objective_instance)
            traces.extend(baseline_traces)
            all_objective.extend(baseline_values)

        if not traces:
            return None

        layout = dict(
            title=self._build_plot_title(objective, plot_config),
            xaxis=dict(title=plot_config.metric_label),
            yaxis=dict(title=plot_config.objective_label),
            legend=_LEGEND_STYLE,
        )
        y_range = self._compute_robust_y_range(all_objective)
        if y_range:
            layout['yaxis']['range'] = y_range
        if known_optimum is not None:
            self._add_optimum_to_layout(layout, known_optimum)
            traces.append(self._optimum_trace(known_optimum))

        self._apply_axis_config(layout, plot_config)
        return go.Figure(data=traces, layout=layout)

    def create_grouped_plot(self, objective: str, experiment_groups: Dict[str, List[Any]],
            plot_config: PlotConfig, extractor: Any,
            baselines: Dict[str, Any] = None,
            title_suffix: str = "",
            known_optimum: Optional[float] = None,
            objective_instance: Optional[str] = None) -> Optional[go.Figure]:
        """Create grouped convergence plot (mean ± std band) or box plot per group.

        The y-axis is auto-scaled to the data range (min/max + 5 % padding).
        A dashed green reference line is drawn at ``known_optimum`` when provided.
        """
        if plot_config.plot_type == 'box_plot':
            return self._create_grouped_box_plot(
                objective, experiment_groups, plot_config, extractor, baselines,
                title_suffix=title_suffix, known_optimum=known_optimum,
                objective_instance=objective_instance)

        traces = []
        all_values = []

        if baselines:
            baseline_traces, baseline_values = self._create_baseline_traces(baselines, objective, objective_instance=objective_instance)
            traces.extend(baseline_traces)
            all_values.extend(baseline_values)

        for group_idx, (group_name, exp_list) in enumerate(experiment_groups.items()):
            color = Constants.DEFAULT_COLORS[group_idx % len(Constants.DEFAULT_COLORS)]
            fill_color = self._hex_to_rgba(color, alpha=0.2)

            grouped_data = extractor.extract_grouped_data(exp_list, objective, plot_config.metric_type)
            if not grouped_data:
                continue
            plot_data = self._prepare_grouped_plot_data(
                grouped_data, min_reps=plot_config.min_reps, min_reps_ratio=plot_config.min_reps_ratio
            )
            if not plot_data:
                continue

            x_vals, mean_y, upper_y, lower_y = plot_data
            all_values.extend(v for v in mean_y + upper_y + lower_y if v is not None)
            traces.extend(self._create_grouped_traces(x_vals, lower_y, upper_y, mean_y, group_name, color, fill_color))

        if not traces:
            return None

        layout = self._create_grouped_layout(objective, plot_config, all_values,
                                             title_suffix=title_suffix, known_optimum=known_optimum)
        if known_optimum is not None:
            self._add_optimum_to_layout(layout, known_optimum)
            traces.append(self._optimum_trace(known_optimum))

        return go.Figure(data=traces, layout=layout)

    def create_grouped_plot_from_series(
        self,
        objective: str,
        grouped_series: Dict[str, Dict[str, Any]],
        plot_config: PlotConfig,
        extractor: Any,
        baselines: Dict[str, Any] = None,
        title_suffix: str = "",
        known_optimum: Optional[float] = None,
        objective_instance: Optional[str] = None,
    ) -> Optional[go.Figure]:
        if plot_config.plot_type == 'box_plot':
            return self.create_grouped_box_plot_from_series(
                objective,
                grouped_series,
                plot_config,
                baselines,
                title_suffix=title_suffix,
                known_optimum=known_optimum,
                objective_instance=objective_instance,
            )

        traces = []
        all_values = []

        if baselines:
            baseline_traces, baseline_values = self._create_baseline_traces(
                baselines, objective, objective_instance=objective_instance
            )
            traces.extend(baseline_traces)
            all_values.extend(baseline_values)

        for group_idx, (group_name, group_data) in enumerate(grouped_series.items()):
            color = Constants.DEFAULT_COLORS[group_idx % len(Constants.DEFAULT_COLORS)]
            fill_color = self._hex_to_rgba(color, alpha=0.2)
            series_list = group_data.get('series_list', [])
            time_series_list = group_data.get('time_series_list', [])

            grouped_data = extractor.extract_grouped_series_data(series_list, plot_config.metric_type, time_series_list)
            if not grouped_data:
                continue
            plot_data = self._prepare_grouped_plot_data(
                grouped_data, min_reps=plot_config.min_reps, min_reps_ratio=plot_config.min_reps_ratio
            )
            if not plot_data:
                continue

            x_vals, mean_y, upper_y, lower_y = plot_data
            all_values.extend(v for v in mean_y + upper_y + lower_y if v is not None)
            traces.extend(self._create_grouped_traces(x_vals, lower_y, upper_y, mean_y, group_name, color, fill_color))

        if not traces:
            return None

        layout = self._create_grouped_layout(
            objective, plot_config, all_values, title_suffix=title_suffix, known_optimum=known_optimum
        )
        if known_optimum is not None:
            self._add_optimum_to_layout(layout, known_optimum)
            traces.append(self._optimum_trace(known_optimum))

        return go.Figure(data=traces, layout=layout)

    def create_scatter_plot_from_series(
        self,
        objective: str,
        grouped_series: Dict[str, Dict[str, Any]],
        plot_config: PlotConfig,
        title_suffix: str = "",
        known_optimum: Optional[float] = None,
        show_mean_line: bool = True,
        axis_bounds: Optional[Any] = None,
    ) -> Optional[go.Figure]:
        """Scatter plot: individual repetition dots + bold mean line per group. No baselines.

        Handles sparse series where ``None`` indicates the LLH was not selected at
        that iteration — only non-None values are plotted as dots, and the mean
        line is computed ignoring None entries.

        When ``show_mean_line`` is False a *pure* scatter is drawn instead: one
        full-opacity ``+`` (cross) marker trace per group covering every point of
        every repetition, and no aggregated mean line. This reproduces the old
        ``sns.relplot(marker="+", hue="Used LLH")`` figures.

        ``axis_bounds`` is an optional ``AxisBounds`` instance that overrides the
        auto-computed axis ranges for the current instance's tab.
        """
        if not show_mean_line:
            return self._create_pure_scatter(
                objective, grouped_series, plot_config,
                title_suffix=title_suffix, known_optimum=known_optimum,
                axis_bounds=axis_bounds,
            )

        traces = []
        all_values = []

        for group_idx, (group_name, group_data) in enumerate(grouped_series.items()):
            color = Constants.DEFAULT_COLORS[group_idx % len(Constants.DEFAULT_COLORS)]
            series_list = group_data.get('series_list', [])
            if not series_list:
                continue

            max_len = max((len(s) for s in series_list if s), default=0)
            if max_len == 0:
                continue

            # Individual repetition traces — faint scatter dots (skip None entries)
            for rep_series in series_list:
                if not rep_series:
                    continue
                x_rep = [i for i, v in enumerate(rep_series) if v is not None and np.isfinite(v)]
                y_rep = [v for v in rep_series if v is not None and np.isfinite(v)]
                if not y_rep:
                    continue
                all_values.extend(y_rep)
                traces.append(go.Scatter(
                    x=x_rep, y=y_rep,
                    mode='markers',
                    marker=dict(size=3, color=color, opacity=0.25),
                    showlegend=False,
                    legendgroup=group_name,
                    hoverinfo='skip',
                ))

            # Mean line — nanmean across repetitions, ignoring None
            arr = np.full((len(series_list), max_len), np.nan)
            for i, s in enumerate(series_list):
                for j, v in enumerate(s):
                    if v is not None and np.isfinite(v):
                        arr[i, j] = float(v)
            import warnings as _w
            with _w.catch_warnings():
                _w.simplefilter("ignore")
                raw_mean = np.nanmean(arr, axis=0)

            x_mean = [i for i, v in enumerate(raw_mean) if not np.isnan(v)]
            y_mean = [float(v) for v in raw_mean if not np.isnan(v)]
            if not y_mean:
                continue
            all_values.extend(y_mean)
            traces.append(go.Scatter(
                x=x_mean, y=y_mean,
                mode='lines+markers',
                name=group_name,
                legendgroup=group_name,
                line=dict(color=color, width=2),
                marker=dict(size=4, color=color),
                hovertemplate='iter %{x}, %{y:.2f}<extra></extra>',
            ))

        if not traces:
            import logging as _logging
            _logging.getLogger(__name__).warning(
                "create_scatter_plot_from_series: no traces produced for objective=%r "
                "(groups=%s). All series may be empty or all-None. "
                "Check extract_llh_series warnings above.",
                objective, list(grouped_series.keys()),
            )
            return None

        layout = dict(
            title=self._build_plot_title(objective, plot_config, title_suffix),
            xaxis=dict(title=plot_config.metric_label),
            yaxis=dict(title=plot_config.objective_label),
            legend=_LEGEND_STYLE,
        )
        self._apply_axis_config(layout, plot_config)
        self._apply_axis_bounds(layout, axis_bounds, all_values)
        if known_optimum is not None:
            self._add_optimum_to_layout(layout, known_optimum)
            traces.append(self._optimum_trace(known_optimum))

        return go.Figure(data=traces, layout=layout)

    def _create_pure_scatter(
        self,
        objective: str,
        grouped_series: Dict[str, Dict[str, Any]],
        plot_config: PlotConfig,
        title_suffix: str = "",
        known_optimum: Optional[float] = None,
        axis_bounds: Optional[Any] = None,
    ) -> Optional[go.Figure]:
        """One full-opacity ``+`` marker trace per group, no mean line.

        Each group's points are pooled across every repetition in
        ``series_list``; ``None`` entries (LLH not selected at that iteration) are
        skipped. The x value is the iteration index within the repetition, the y
        value the raw objective — mirroring the old per-iteration LLH scatter.
        """
        traces = []
        all_values = []

        for group_idx, (group_name, group_data) in enumerate(grouped_series.items()):
            color = Constants.DEFAULT_COLORS[group_idx % len(Constants.DEFAULT_COLORS)]
            series_list = group_data.get('series_list', [])
            x_all, y_all = [], []
            for rep_series in series_list:
                if not rep_series:
                    continue
                for i, v in enumerate(rep_series):
                    if v is not None and np.isfinite(v):
                        x_all.append(i)
                        y_all.append(v)
            if not y_all:
                continue
            all_values.extend(y_all)
            traces.append(go.Scatter(
                x=x_all, y=y_all,
                mode='markers',
                name=group_name,
                legendgroup=group_name,
                marker=dict(size=7, color=color, symbol='cross', opacity=0.8),
                hovertemplate='iter %{x}, %{y:.2f}<extra></extra>',
            ))

        if not traces:
            import logging as _logging
            _logging.getLogger(__name__).warning(
                "_create_pure_scatter: no traces produced for objective=%r (groups=%s).",
                objective, list(grouped_series.keys()),
            )
            return None

        layout = dict(
            title=self._build_plot_title(objective, plot_config, title_suffix),
            xaxis=dict(title=plot_config.metric_label),
            yaxis=dict(title=plot_config.objective_label),
            legend=_LEGEND_STYLE,
        )
        self._apply_axis_config(layout, plot_config)
        self._apply_axis_bounds(layout, axis_bounds, all_values)
        if known_optimum is not None:
            self._add_optimum_to_layout(layout, known_optimum)
            traces.append(self._optimum_trace(known_optimum))

        return go.Figure(data=traces, layout=layout)

    def create_grouped_box_plot_from_series(
        self,
        objective: str,
        grouped_series: Dict[str, Dict[str, Any]],
        plot_config: PlotConfig,
        baselines: Dict[str, Any] = None,
        title_suffix: str = "",
        known_optimum: Optional[float] = None,
        objective_instance: Optional[str] = None,
    ) -> Optional[go.Figure]:
        traces = []
        all_values = []

        if baselines:
            for baseline_key, baseline_result in baselines.items():
                baseline_values = self._extract_baseline_values(
                    baseline_result,
                    objective,
                    objective_instance=objective_instance,
                    extractor=None,
                )
                if baseline_values:
                    all_values.extend(baseline_values)
                    baseline_name = self.parser.build_display_name(baseline_key)
                    traces.append(go.Box(
                        y=baseline_values,
                        name=baseline_name,
                        boxmean=False,
                        boxpoints=False,
                        marker=dict(opacity=0.5, color='gray'),
                        hovertemplate='%{y:.4f}<extra></extra>'
                    ))

        for group_idx, (group_name, group_data) in enumerate(grouped_series.items()):
            final_values = group_data.get('final_values', [])
            if final_values:
                color = Constants.DEFAULT_COLORS[group_idx % len(Constants.DEFAULT_COLORS)]
                all_values.extend(final_values)
                traces.append(go.Box(
                    y=final_values,
                    name=group_name,
                    boxmean=False,
                    boxpoints=False,
                    marker=dict(opacity=0.7, color=color),
                    line=dict(color=color),
                    hovertemplate='%{y:.4f}<extra></extra>'
                ))

        if not traces:
            return None

        layout = dict(
            title=self._build_plot_title(objective, plot_config, title_suffix),
            xaxis=dict(title='Test Case', automargin=True),
            yaxis=dict(title=plot_config.objective_label, automargin=True),
            showlegend=True, boxmode='overlay',
            margin=dict(l=70, r=40, t=80, b=110),
            legend=_LEGEND_STYLE,
        )
        range_values = all_values
        if known_optimum is not None:
            range_values = all_values + [known_optimum]
        y_range = self._compute_robust_y_range(range_values, padding_ratio=0.12)
        if y_range:
            layout['yaxis']['range'] = y_range
        if known_optimum is not None:
            self._add_optimum_to_layout(layout, known_optimum)
            traces.append(self._optimum_trace(known_optimum))

        self._apply_axis_config(layout, plot_config)
        return go.Figure(data=traces, layout=layout)

    @staticmethod
    def _prepare_grouped_plot_data(grouped_data: Dict[str, Any],
                                   min_reps: int = 1,
                                   min_reps_ratio: Optional[float] = None) -> Optional[Tuple[List, List, List, List]]:
        """Return ``(x_vals, mean_y, upper_y, lower_y)`` where the band is mean ± std.

        Indices with fewer than the computed threshold of repetitions contributing
        (per ``grouped_data['sample_counts']``) are dropped, trimming sparsely-sampled
        tails where only a few long-running reps survive.

        When ``min_reps_ratio`` is set (0.0–1.0) the threshold is computed as
        ``max(1, round(n_reps * min_reps_ratio))`` where ``n_reps`` is the maximum
        sample count across all indices.  This adapts to the actual group size so
        that, e.g., a ratio of 0.5 always requires at least half the repetitions
        regardless of how many there are.  ``min_reps`` is ignored when the ratio
        is set.
        """
        metric_vals = grouped_data['metric_values']
        mean_vals = grouped_data['mean_values']
        std_vals = grouped_data.get('std_values', [None] * len(mean_vals))
        sample_counts = grouped_data.get('sample_counts', [None] * len(mean_vals))

        threshold = compute_rep_threshold(min_reps, min_reps_ratio, sample_counts)

        valid_indices = [
            i for i in range(len(metric_vals))
            if metric_vals[i] is not None and mean_vals[i] is not None
            and (sample_counts[i] is None or sample_counts[i] >= threshold)
        ]
        if not valid_indices:
            return None

        x_vals = [metric_vals[i] for i in valid_indices]
        mean_y = [mean_vals[i] for i in valid_indices]
        std_y = [std_vals[i] if std_vals[i] is not None else 0.0 for i in valid_indices]

        return x_vals, mean_y, [m + s for m, s in zip(mean_y, std_y)], [m - s for m, s in zip(mean_y, std_y)]

    @staticmethod
    def _create_grouped_traces(x_vals: List, lower_y: List, upper_y: List, mean_y: List,
            group_name: str, color: str, fill_color: str) -> List[go.Scatter]:
        """Three traces per group: invisible upper bound, ±std shaded band, mean line.

        Only the mean line appears in the legend (one entry per group).
        The std band is linked to the same legend group so hovering highlights both.
        """
        return [
            go.Scatter(x=x_vals, y=upper_y, mode='lines', line=dict(width=0),
                showlegend=False, hoverinfo='skip', legendgroup=group_name),
            go.Scatter(x=x_vals, y=lower_y, mode='lines', line=dict(width=0),
                fill='tonexty', fillcolor=fill_color,
                showlegend=False, hovertemplate='%{x}, %{y:.4f}<extra></extra>',
                legendgroup=group_name),
            go.Scatter(x=x_vals, y=mean_y, mode='lines+markers',
                name=group_name, line=dict(color=color), marker=dict(color=color),
                hovertemplate='%{x}, %{y:.4f}<extra></extra>', legendgroup=group_name),
        ]

    def _create_grouped_layout(self, objective: str, plot_config: PlotConfig, all_values: List[float],
                                title_suffix: str = "",
                                known_optimum: Optional[float] = None) -> Dict[str, Any]:
        layout = dict(
            title=self._build_plot_title(objective, plot_config, title_suffix),
            xaxis=dict(title=plot_config.metric_label),
            yaxis=dict(title=plot_config.objective_label),
            legend=_LEGEND_STYLE,
        )
        self._apply_axis_config(layout, plot_config)
        y_range = self._compute_robust_y_range(all_values)
        if y_range:
            layout['yaxis']['range'] = y_range
        return layout

    def _create_grouped_box_plot(self, objective: str, experiment_groups: Dict[str, List[Any]],
                                 plot_config: PlotConfig, extractor: Any,
                                 baselines: Dict[str, Any] = None,
                                 title_suffix: str = "",
                                 known_optimum: Optional[float] = None,
                                 objective_instance: Optional[str] = None) -> Optional[go.Figure]:
        traces = []
        all_values = []

        if baselines:
            for baseline_key, baseline_result in baselines.items():
                baseline_values = self._extract_baseline_values(
                    baseline_result,
                    objective,
                    objective_instance=objective_instance,
                    extractor=extractor,
                )
                if baseline_values:
                    all_values.extend(baseline_values)
                    baseline_name = self.parser.build_display_name(baseline_key)
                    traces.append(go.Box(
                        y=baseline_values,
                        name=baseline_name,
                        boxmean=False,
                        boxpoints=False,
                        marker=dict(opacity=0.5, color='gray'),
                        hovertemplate='%{y:.4f}<extra></extra>'
                    ))

        for group_idx, (group_name, exp_list) in enumerate(experiment_groups.items()):
            group_values = []
            for exp in exp_list:
                trajectory = extractor.extract_objective_series(exp, objective)
                if trajectory:
                    final_value = trajectory[-1]
                    if final_value is not None and np.isfinite(final_value):
                        group_values.append(final_value)
            if group_values:
                color = Constants.DEFAULT_COLORS[group_idx % len(Constants.DEFAULT_COLORS)]
                all_values.extend(group_values)
                traces.append(go.Box(
                    y=group_values,
                    name=group_name,
                    boxmean=False,
                    boxpoints=False,
                    marker=dict(opacity=0.7, color=color),
                    line=dict(color=color),
                    hovertemplate='%{y:.4f}<extra></extra>'
                ))

        if not traces:
            return None

        layout = dict(
            title=self._build_plot_title(objective, plot_config, title_suffix),
            xaxis=dict(title='Test Case', automargin=True),
            yaxis=dict(title=plot_config.objective_label, automargin=True),
            showlegend=True, boxmode='overlay',
            margin=dict(l=70, r=40, t=80, b=110),
            legend=_LEGEND_STYLE,
        )
        range_values = all_values
        if known_optimum is not None:
            range_values = all_values + [known_optimum]
        y_range = self._compute_robust_y_range(range_values, padding_ratio=0.12)
        if y_range:
            layout['yaxis']['range'] = y_range
        if known_optimum is not None:
            self._add_optimum_to_layout(layout, known_optimum)
            traces.append(self._optimum_trace(known_optimum))

        self._apply_axis_config(layout, plot_config)
        return go.Figure(data=traces, layout=layout)

    @staticmethod
    def _extract_baseline_values(
        baseline_result: Any,
        objective: str,
        objective_instance: Optional[str] = None,
        extractor: Optional[Any] = None,
        full_run: bool = False,
    ) -> List[float]:
        def _reduce(trajectory: Optional[List[float]]) -> List[float]:
            if not trajectory:
                return []
            if full_run:
                return [v for v in trajectory if v is not None and np.isfinite(v)]
            final_value = trajectory[-1]
            if final_value is not None and np.isfinite(final_value):
                return [final_value]
            return []

        # Full-run distribution: use the same (possibly normalized) trajectory the
        # other plots use, so the baseline box stays on the same scale as the
        # normalized experiment series instead of falling back to raw values.
        if full_run:
            cache_key = objective_instance or objective
            return _reduce(extract_baseline_trajectory(
                baseline_result,
                cache_key,
                prefer_cached=True,
                best_so_far_fallback=True,
                minimize=True,
                result_key=objective,
            ))

        raw_experiments = getattr(baseline_result, 'raw_experiments', None)
        if raw_experiments:
            filtered_experiments = raw_experiments
            if objective_instance:
                try:
                    from analyzer.data_pipeline.experiment_metadata import ExperimentMetadata
                    instance_matches = [
                        exp for exp in raw_experiments
                        if ExperimentMetadata.extract(exp).get("problem_instance") == objective_instance
                    ]
                    if instance_matches:
                        filtered_experiments = instance_matches
                except Exception:
                    pass
            values: List[float] = []
            for exp in filtered_experiments:
                if extractor is not None:
                    trajectory = extractor.extract_objective_series(exp, objective)
                else:
                    trajectory = extract_best_so_far_series(
                        exp, objective, minimize=True, only_enabled_improves=False
                    )
                values.extend(_reduce(trajectory))
            return values

        raw_experiment = getattr(baseline_result, 'raw_experiment', None)
        if raw_experiment is not None:
            if extractor is not None:
                trajectory = extractor.extract_objective_series(raw_experiment, objective)
            else:
                trajectory = extract_best_so_far_series(
                    raw_experiment, objective, minimize=True, only_enabled_improves=False
                )
            return _reduce(trajectory)

        cache_key = objective_instance or objective
        trajectory = extract_baseline_trajectory(
            baseline_result,
            cache_key,
            prefer_cached=True,
            best_so_far_fallback=True,
            minimize=True,
            result_key=objective,
        )
        return _reduce(trajectory)

    def create_box_plot(self, objective: str, experiment_names: List[str], data_series: List[List[float]],
            plot_config: PlotConfig, baselines: Dict[str, Any] = None,
            known_optimum: Optional[float] = None,
            objective_instance: Optional[str] = None) -> go.Figure:
        traces = []
        all_values = []

        # Without grouping, each box shows the objective distribution of an
        # approach over its whole run (where it started -> where it finished),
        # pooled across repetitions sharing a display name. Using only the final
        # value would collapse the box to a single flat line.
        values_by_name: "OrderedDict[str, List[float]]" = OrderedDict()
        for series, name in zip(data_series, experiment_names):
            if not series:
                continue
            finite = [v for v in series if v is not None and np.isfinite(v)]
            if not finite:
                continue
            values_by_name.setdefault(name, []).extend(finite)

        for name, values in values_by_name.items():
            all_values.extend(values)
            traces.append(go.Box(
                y=values,
                name=name,
                boxmean=False,
                boxpoints=False,
                marker=dict(opacity=0.7),
                hovertemplate='%{y:.4f}<extra></extra>'
            ))

        if baselines:
            for baseline_key, baseline_result in baselines.items():
                # No grouping: show the baseline's full-run distribution too,
                # matching the experiment boxes above.
                baseline_values = self._extract_baseline_values(
                    baseline_result,
                    objective,
                    objective_instance=objective_instance,
                    extractor=None,
                    full_run=True,
                )
                if baseline_values:
                    all_values.extend(baseline_values)
                    display_name = self.parser.build_display_name(baseline_key)
                    traces.append(go.Box(
                        y=baseline_values,
                        name=display_name,
                        boxmean=False,
                        boxpoints=False,
                        marker=dict(opacity=0.6, color='#808080'),
                        line=dict(color='#606060'),
                        hovertemplate='%{y:.4f}<extra></extra>'
                    ))

        layout = dict(
            title=self._build_plot_title(objective, plot_config),
            xaxis=dict(title='Algorithm', automargin=True),
            yaxis=dict(title=plot_config.objective_label, automargin=True),
            showlegend=True, boxmode='overlay',
            margin=dict(l=70, r=40, t=80, b=110),
            legend=_LEGEND_STYLE,
        )
        range_values = all_values
        if known_optimum is not None:
            range_values = all_values + [known_optimum]
        y_range = self._compute_robust_y_range(range_values, padding_ratio=0.12)
        if y_range:
            layout['yaxis']['range'] = y_range
        if known_optimum is not None:
            self._add_optimum_to_layout(layout, known_optimum)
            traces.append(self._optimum_trace(known_optimum))

        self._apply_axis_config(layout, plot_config)

        return go.Figure(data=traces, layout=layout)
