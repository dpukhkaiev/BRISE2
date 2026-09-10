from typing import List, Dict, Optional, Tuple
import numpy as np
import plotly.graph_objs as go

from analyzer.comparison.comparison_processor import ComparisonResult
from analyzer.config.benchmark_config import Constants
from analyzer.data_pipeline import ExperimentParser


class ComparativePlotGenerator:
    """Generator for comparative analysis plots"""

    def __init__(self):
        self.parser = ExperimentParser()

    def plot_regret_curves(
        self,
        comparison_results: List[ComparisonResult],
        title: str = "Regret Curves",
        log_scale: bool = False,
        regret_type: str = "iteration"
    ) -> Optional[go.Figure]:
        traces = []
        seen_experiments = {}
        seen_baselines = {}
        for result in comparison_results:
            raw_name = result.display_name or result.experiment_name
            exp_name = self.parser.build_display_name(raw_name)
            if exp_name not in seen_experiments:
                seen_experiments[exp_name] = result
            if result.baseline_type and result.baseline_type not in seen_baselines:
                seen_baselines[result.baseline_type] = result

        for idx, (baseline_type, result) in enumerate(seen_baselines.items()):
            baseline_label = self.parser.build_display_name(baseline_type)
            color = self.BASELINE_COLORS[idx % len(self.BASELINE_COLORS)]
            if regret_type == "time":
                curve = result.baseline_regret_curve_time
                if not curve:
                    continue
                x_vals = [t for t, _ in curve]
                y_vals = [r for _, r in curve]
            else:
                curve = result.baseline_regret_curve
                if not curve:
                    continue
                x_vals = list(range(len(curve)))
                y_vals = curve

            traces.append(go.Scatter(
                x=x_vals, y=y_vals, mode='lines', name=baseline_label,
                line=dict(color=color, dash='dash', width=2.5)
            ))

        for idx, (exp_name, result) in enumerate(seen_experiments.items()):
            color = Constants.DEFAULT_COLORS[idx % len(Constants.DEFAULT_COLORS)]
            if regret_type == "time":
                if result.regret_curve_time is None:
                    continue
                x_vals = [t for t, _ in result.regret_curve_time]
                y_vals = [r for _, r in result.regret_curve_time]
            else:
                if result.regret_curve is None:
                    continue
                x_vals = list(range(len(result.regret_curve)))
                y_vals = result.regret_curve

            traces.append(go.Scatter(
                x=x_vals, y=y_vals, mode='lines+markers', name=exp_name,
                line=dict(color=color), marker=dict(size=4)
            ))

        if not traces:
            return None

        layout = dict(
            title=title,
            xaxis=dict(title='Time (seconds)' if regret_type == "time" else 'Iteration'),
            yaxis=dict(title='Regret (distance to optimum)'),
            hovermode='closest', showlegend=True
        )
        if log_scale:
            layout['yaxis']['type'] = 'log'

        return go.Figure(data=traces, layout=layout)

    BASELINE_COLORS = ['#888888', '#555555', '#2d2d2d', '#aaaaaa', '#666666']

    _IMPROVEMENT_BAR_COLOR = '#1f77b4'

    def plot_relative_improvement(
        self,
        comparison_results: List[ComparisonResult],
        title: str = "Relative Improvement",
        improvement_type: str = "objective_value"
    ) -> Optional[go.Figure]:
        improvement_attr = {
            "objective_value": "relative_improvement",
            "time_to_target": "relative_improvement_time",
            "iteration_to_target": "relative_improvement_iterations"
        }
        attr_name = improvement_attr.get(improvement_type, "relative_improvement")
        is_ratio_based = improvement_type in ["objective_value", "time_to_target", "iteration_to_target"]
        ratio_labels = {
            "objective_value": "Objective Ratio (base/exp)",
            "time_to_target": "Time Ratio (exp/base)",
            "iteration_to_target": "Iteration Ratio (exp/base)",
        }

        experiment_names, improvements, baseline_types = [], [], []
        for result in comparison_results:
            value = getattr(result, attr_name, None)
            if value is not None:
                exp_name = result.display_name or result.experiment_name
                experiment_names.append(self.parser.build_display_name(exp_name))
                improvements.append(value)
                baseline_types.append(result.baseline_type)

        if not improvements:
            return None

        baseline_type_groups = {}
        for name, improvement, baseline in zip(experiment_names, improvements, baseline_types):
            baseline_type_groups.setdefault(baseline, {'names': [], 'improvements': []})
            baseline_type_groups[baseline]['names'].append(name)
            baseline_type_groups[baseline]['improvements'].append(improvement)

        ordered_experiments = list(dict.fromkeys(experiment_names))
        traces = []
        aligned_values: List[float] = []

        for idx, (baseline_type, data) in enumerate(baseline_type_groups.items()):
            color = self.BASELINE_COLORS[idx % len(self.BASELINE_COLORS)]
            imp_map = dict(zip(data['names'], data['improvements']))
            aligned_y = [imp_map.get(exp) for exp in ordered_experiments]
            aligned_values.extend([v for v in aligned_y if v is not None and np.isfinite(v)])
            text_labels = [
                f"{val:.2f}x" if (val is not None and abs(val) >= 0.1) else ''
                for val in aligned_y
            ]

            baseline_label = self.parser.build_display_name(baseline_type)
            traces.append(go.Bar(
                x=ordered_experiments,
                y=aligned_y,
                name=f"vs {baseline_label}",
                marker=dict(color=self._IMPROVEMENT_BAR_COLOR, line=dict(color=self._IMPROVEMENT_BAR_COLOR, width=1)),
                text=text_labels,
                textposition='outside',
                textfont=dict(size=12, color='#2c3e50'),
                offsetgroup=str(idx),
                cliponaxis=False,
            ))

        finite_vals = aligned_values
        if not finite_vals:
            return None
        min_val, max_val = min(finite_vals), max(finite_vals)
        if is_ratio_based:
            center = 1.0
            span = max(abs(min_val - center), abs(max_val - center), 0.2)
            y_min = max(0.0, center - 1.2 * span)
            y_max = center + 1.2 * span
        else:
            center = 0.0
            span = max(abs(min_val - center), abs(max_val - center), 0.1)
            y_min = center - 1.2 * span
            y_max = center + 1.2 * span

        data_pad = 0.1 * (max_val - min_val) if max_val != min_val else 0.1 * (abs(max_val) if max_val != 0 else 1.0)
        y_min = min(y_min, min_val - data_pad)
        y_max = max(y_max, max_val + data_pad)

        y_axis_min = max(0.0, y_min) if is_ratio_based else y_min

        layout = dict(
            title=title,
            xaxis=dict(title='Experiment', tickangle=45, automargin=True),
            yaxis=dict(
                title=ratio_labels.get(improvement_type, 'Relative Improvement'),
                range=[y_axis_min, y_max],
                automargin=True,
            ),
            barmode='group',
            bargap=0.2,
            bargroupgap=0.05,
            showlegend=True,
            legend=dict(
                orientation='v', yanchor='top', y=1, xanchor='right', x=1.15,
            ),
            margin=dict(l=70, r=140, t=80, b=170),
        )
        if is_ratio_based:
            layout['shapes'] = [dict(
                type='line', xref='paper', x0=0, x1=1,
                yref='y', y0=1.0, y1=1.0,
                line=dict(color='gray', dash='dot', width=1.5),
            )]

        return go.Figure(data=traces, layout=layout)


    def plot_performance_profile(
        self,
        performance_profiles: Dict[str, Tuple[np.ndarray, np.ndarray]],
        title: str = "Performance Profile"
    ) -> Optional[go.Figure]:
        if not performance_profiles:
            return None

        traces = []
        for idx, (test_case_name, (tau_values, rho_values)) in enumerate(performance_profiles.items()):
            color = Constants.DEFAULT_COLORS[idx % len(Constants.DEFAULT_COLORS)]
            traces.append(go.Scatter(
                x=tau_values.tolist(), y=rho_values.tolist(),
                mode='lines+markers', name=test_case_name,
                line=dict(color=color, width=2),
                marker=dict(size=4)
            ))

        all_tau_max = max(max(tau) for tau, _ in performance_profiles.values())

        layout = dict(
            title=title,
            xaxis=dict(title='Performance Ratio (τ)', range=[1, min(all_tau_max, 10)]),
            yaxis=dict(title='Fraction of Problems Solved (ρ)', range=[0, 1.05]),
            hovermode='closest', showlegend=True,
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="right", x=1)
        )

        return go.Figure(data=traces, layout=layout)
