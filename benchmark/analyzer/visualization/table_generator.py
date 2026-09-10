import math
from typing import List, Dict, Any, Set, Optional, Tuple

from analyzer.config.benchmark_config import TableConfig
from analyzer.data_pipeline import ExperimentParser, MetricExtractor


class TableGenerator:
    """Builds data tables for the report"""

    COLUMN_MAP = {'task': 'Task', 'model': 'Model', 'sampler': 'Sampler',
        'configuration_strategy': 'ConfigurationStrategy', 'stop_condition': 'StopCondition', 'test_case': 'TestCase',
        'experiment': 'Experiment', 'objective': 'Objective', 'iterations': 'Iterations', 'initial_value': 'Initial',
        'final_best_value': 'Final best', 'improvement_percentage': 'Improvement %',
        'improvement_absolute': 'Absolute improvement', 'runtime': 'Runtime (s)'}

    PREFERRED_COLUMN_ORDER = ['Task', 'Model', 'Sampler', 'ConfigurationStrategy', 'StopCondition', 'TestCase',
        'Experiment', 'Objective', 'Iterations', 'Initial', 'Final best', 'Absolute improvement', 'Improvement %',
        'Runtime (s)']

    def __init__(self, parser: ExperimentParser, extractor: MetricExtractor):
        self.parser = parser
        self.extractor = extractor

    def create_table(self, experiments: List[Any], objective: str, table_config: TableConfig,
                     comparative_data: Optional[Dict[str, Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Build summary table for a specific objective"""
        rows = []
        for exp in experiments:
            exp_name = self.parser.get_name(exp)
            comp_data = comparative_data.get(exp_name) if comparative_data else None
            row = self._build_experiment_row(exp, objective, table_config, comp_data)
            if row:
                rows.append(row)
        return rows

    def build_row(self, exp: Any, objective: str, table_config: TableConfig) -> Optional[Dict[str, Any]]:
        return self._build_experiment_row(exp, objective, table_config)

    def _build_experiment_row(self, exp: Any, objective: str, table_config: TableConfig,
                             comparative_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Build table row for single experiment"""
        values = self.extractor.extract_objective_series(exp, objective)
        if not values:
            return None

        # extract_objective_series already returns the best-so-far series;
        # values[0] is the initial value, values[-1] is the cumulative best.
        initial = values[0]
        final_best = values[-1]

        improvement_abs, improvement_pct = self._compute_improvement(initial, final_best)

        exp_name = self.parser.get_name(exp)
        features = self.parser.parse_features_from_experiment(exp)
        runtime = self.extractor.extract_runtime(exp)

        row = {'Task': features.get('Task'), 'Model': features.get('Model'), 'Sampler': features.get('Sampler'),
            'ConfigurationStrategy': features.get('ConfigurationStrategy'),
            'StopCondition': features.get('StopCondition'), 'TestCase': features.get('TestCase'),
            'Experiment': self.parser.build_display_name(exp_name), 'Objective': objective, 'Iterations': len(values),
            'Initial': initial, 'Final best': final_best, 'Absolute improvement': improvement_abs,
            'Improvement %': round(improvement_pct, 2) if improvement_pct is not None else None, 'Runtime (s)': runtime}

        # Add comparative metrics if available
        if comparative_data:
            row['Regret (final)'] = self._format_metric(comparative_data.get('regret_final'))
            row['Rel. Improvement'] = self._format_percentage(comparative_data.get('relative_improvement'))
            row['Performance Ratio'] = self._format_metric(comparative_data.get('performance_ratio'))

        return row

    @staticmethod
    def _format_metric(value: Optional[float], decimals: int = 4) -> Optional[float]:
        """Format a metric value"""
        if value is None or not math.isfinite(value):
            return None
        return round(value, decimals)

    @staticmethod
    def _format_percentage(value: Optional[float]) -> Optional[str]:
        """Format a percentage value"""
        if value is None or not math.isfinite(value):
            return None
        return f"{value * 100:.2f}%"

    @staticmethod
    def _format_speedup(value: Optional[float]) -> Optional[str]:
        """Format a speedup value"""
        if value is None or not math.isfinite(value) or value <= 0:
            return None
        return f"{value:.2f}x"

    @staticmethod
    def _compute_improvement(initial: Optional[float], final: Optional[float]) -> Tuple[
        Optional[float], Optional[float]]:
        """Compute absolute and percentage improvement"""
        if initial is None or final is None:
            return None, None

        improvement_abs = initial - final
        improvement_pct = (improvement_abs / initial * 100) if initial != 0 else None

        return improvement_abs, improvement_pct

    def format_table(self, rows: List[Dict[str, Any]], table_config: TableConfig) -> str:
        """Format table rows as HTML with column filtering"""
        if not rows:
            return ""

        allowed_columns = self._get_allowed_columns(table_config)
        headers = self._order_headers(rows, allowed_columns)

        html_parts = ["<table class='summary-table'>", self._build_header_row(headers)]
        html_parts.extend(self._build_data_rows(rows, headers))
        html_parts.append("</table>")

        return ''.join(html_parts)

    def format_comparative_table(self, rows: List[Dict[str, Any]]) -> str:
        """Format comparative metrics table rows as HTML"""
        if not rows:
            return ""

        preferred_order = [
            'Experiment', 'Baseline', 'Rel. Improvement', 'Speedup Factor',
            'Converged at Iter', 'Experiment Best', 'Baseline Best', 'Final Regret',
            'RI (Objective)', 'RI (Time)', 'RI (Iterations)',
        ]
        all_keys: set = set().union(*(row.keys() for row in rows))
        headers = [h for h in preferred_order if h in all_keys]
        headers += sorted(k for k in all_keys if k not in headers)

        html_parts = [
            "<div class='table-wrapper'>",
            "<table class='summary-table'>",
            self._build_header_row(headers),
        ]
        html_parts.extend(self._build_data_rows(rows, headers))
        html_parts += ["</table>", "</div>"]

        return ''.join(html_parts)

    @staticmethod
    def _get_allowed_columns(table_config: TableConfig) -> Set[str]:
        """Get set of allowed columns based on config"""
        allowed = set()
        for config_field, column_name in TableGenerator.COLUMN_MAP.items():
            if getattr(table_config, config_field, True):
                allowed.add(column_name)
        return allowed

    def _order_headers(self, rows: List[Dict[str, Any]], allowed_columns: Set[str]) -> List[str]:
        """Order headers according to preferred order"""
        all_columns = set()
        for row in rows:
            all_columns.update(row.keys())

        headers = [h for h in self.PREFERRED_COLUMN_ORDER if h in all_columns and h in allowed_columns]
        headers += [c for c in sorted(all_columns) if c not in headers and c in allowed_columns]

        return headers

    @staticmethod
    def _build_header_row(headers: List[str]) -> str:
        """Build HTML header row"""
        return '<tr>' + ''.join(f'<th>{h}</th>' for h in headers) + '</tr>'

    @staticmethod
    def _build_data_rows(rows: List[Dict[str, Any]], headers: List[str]) -> List[str]:
        """Build HTML data rows"""
        html_rows = []
        for row in rows:
            cells = []
            for header in headers:
                value = TableGenerator._format_value(row.get(header))
                css_class = 'exp-name' if header == 'Experiment' else 'num'
                cells.append(f"<td class='{css_class}'>{value}</td>")

            html_rows.append('<tr>' + ''.join(cells) + '</tr>')

        return html_rows

    @staticmethod
    def _format_value(val: Any) -> str:
        """Format value for HTML display"""
        if val is None:
            return ''
        if isinstance(val, float):
            if math.isnan(val):
                return ''
            return f"{val:.4g}"
        return str(val)
