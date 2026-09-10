from datetime import datetime
from typing import Dict, List, Any, Optional

import plotly.graph_objs as go

from analyzer.config.benchmark_config import BenchmarkConfig
from analyzer.visualization.table_generator import TableGenerator
from template.template_loader import TemplateLoader


class ReportGenerator:
    def __init__(self, config: BenchmarkConfig, table_generator: TableGenerator):
        self.config = config
        self.table_generator = table_generator
        self.template_loader = TemplateLoader()

    def generate(self,
                 objective_plots: Dict[str, List[go.Figure]],
                 table_data: Dict[str, List[Dict[str, Any]]],
                 csv_files: Dict[str, str],
                 zip_file: Optional[str],
                 comparative_plots: Optional[Dict[str, List[go.Figure]]] = None,
                 comparative_tables: Optional[Dict[str, List[Dict[str, Any]]]] = None,
                 performance_profile_plot: Optional[go.Figure] = None,
                 comparative_csv_files: Optional[Dict[str, str]] = None) -> str:
        """Generate complete HTML report. One tab per objective."""
        tab_buttons: List[str] = []
        tab_contents: List[str] = []

        for idx, (objective, figures) in enumerate(objective_plots.items()):
            tab_id = f"obj_tab_{idx}"
            active_class = "active" if idx == 0 else ""
            tab_buttons.append(self._tab_button(objective, tab_id, active_class))
            tab_contents.append(self._tab_content(
                objective, figures, table_data, csv_files, tab_id, idx == 0,
                (comparative_plots or {}).get(objective, []),
                (comparative_tables or {}).get(objective, []),
                (comparative_csv_files or {}),
            ))

        # Performance Profile tab
        if performance_profile_plot:
            tab_id = "performance_profile_tab"
            is_first_tab = not tab_buttons
            active_class = "active" if is_first_tab else ""
            tab_buttons.append(self._tab_button("Performance Profile", tab_id, active_class))
            tab_contents.append(self._performance_profile_tab(
                performance_profile_plot, tab_id, is_first_tab
            ))

        global_download = self._global_download(zip_file)
        tabs_html = (f"<div class='tabs'>{global_download}"
                     f"<div class='tab-buttons'>{''.join(tab_buttons)}</div>"
                     f"{''.join(tab_contents)}</div>")

        context = {
            "generated_time": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "experiment_name": self.config.experiment_name,
            "experiment_description": self.config.experiment_description,
            "objectives": ", ".join(objective_plots.keys()),
            "tabs_section": tabs_html,
        }
        return self.template_loader.render_template(
            "report_template.html", context=context,
            css_files=["report.css"], js_files=["report.js"]
        )

    def _tab_content(self, objective: str, figures: List[go.Figure],
                     table_data: Dict[str, List[Dict[str, Any]]],
                     csv_files: Dict[str, str], tab_id: str, is_active: bool,
                     comp_figures: List[go.Figure],
                     comp_table_rows: List[Dict[str, Any]],
                     comparative_csv_files: Dict[str, str]) -> str:
        parts = [f"<div id='{tab_id}' class='tab-content' "
                 f"style='display:{'block' if is_active else 'none'}'>",
                 self._render_figures(objective, figures, tab_id)]
        if comp_figures or comp_table_rows:
            parts.append(self._comparative_section(
                objective,
                comp_figures,
                comp_table_rows,
                comparative_csv_files,
                tab_id,
            ))
        parts.append(self._csv_download(objective, csv_files))
        table_html = self.table_generator.format_table(table_data.get(objective, []), self.config.table_config)
        if table_html:
            parts.append(f"<div class='table-wrapper'>{table_html}</div>")
        parts.append("</div>")
        return "".join(parts)

    def _performance_profile_tab(self, fig: go.Figure, tab_id: str, is_active: bool) -> str:
        plot_id = f"plot_{tab_id}_0"
        display = "block" if is_active else "none"
        return (f"<div id='{tab_id}' class='tab-content' style='display:{display}'>"
                f"<div class='plot-container'><div class='plot-wrapper' id='{plot_id}'>"
                f"{fig.to_html(include_plotlyjs=False, full_html=False)}"
                f"</div><button class='export-btn' "
                f"onclick='exportPlotAsSVG(\"{plot_id}\",\"performance_profile\")'>Export as SVG</button>"
                f"</div></div>")

    def _comparative_section(self, objective: str, figures: List[go.Figure],
                              table_rows: List[Dict[str, Any]],
                              comparative_csv_files: Dict[str, str], tab_id: str) -> str:
        parts = ["<div class='comparative-section'>"]
        for i in range(len(figures)):
            fig = figures[i]
            plot_id = f"comp_plot_{tab_id}_{i}"
            parts.append(
                f"<div class='plot-container'><div class='plot-wrapper' id='{plot_id}'>"
                f"{fig.to_html(include_plotlyjs=False, full_html=False)}"
                f"</div><button class='export-btn' "
                f"onclick='exportPlotAsSVG(\"{plot_id}\",\"{objective}_comparative_{i}\")'>Export as SVG</button>"
                f"</div>"
            )
            figures[i] = None
        if table_rows and self._show_comparative_table():
            parts.append(self._csv_download(
                objective,
                comparative_csv_files,
                link_text=f"Download Comparative {objective} CSV",
            ))
            parts.append(self.table_generator.format_comparative_table(table_rows))
        parts.append("</div>")
        return "".join(parts)

    @staticmethod
    def _render_figures(objective: str, figures: List[go.Figure], id_prefix: str) -> str:
        parts = []
        for i in range(len(figures)):
            fig = figures[i]
            plot_id = f"plot_{id_prefix}_{i}"
            parts.append(
                f"<div class='plot-container'><div class='plot-wrapper' id='{plot_id}'>"
                f"{fig.to_html(include_plotlyjs=False, full_html=False)}"
                f"</div><button class='export-btn' "
                f"onclick='exportPlotAsSVG(\"{plot_id}\",\"{objective}_plot{i}\")'>Export as SVG</button>"
                f"</div>"
            )
            figures[i] = None
        return "".join(parts)

    @staticmethod
    def _tab_button(label: str, tab_id: str, active_class: str) -> str:
        return f"<button class='tab-btn {active_class}' onclick=showTab('{tab_id}',this)>{label}</button>"

    @staticmethod
    def _csv_download(objective: str, csv_files: Dict[str, str], link_text: Optional[str] = None) -> str:
        fname = csv_files.get(objective, "")
        if not fname:
            return ""
        text = link_text or f"Download {objective} CSV"
        return (f"<div class='download-row'>"
                f"<a class='download-link' href='{fname}' download>{text}</a>"
                f"</div>")

    @staticmethod
    def _global_download(zip_file: Optional[str]) -> str:
        if not zip_file:
            return ""
        return (f"<div class='global-download'>"
                f"<a class='download-link all' href='{zip_file}' download>Download all tables (.zip)</a>"
                f"</div>")

    def _show_comparative_table(self) -> bool:
        if hasattr(self.config, "comparative_analysis") and self.config.comparative_analysis:
            return getattr(self.config.comparative_analysis, "show_summary_table", True)
        return True