import json
from copy import deepcopy
from pathlib import Path

from analyzer.config import BenchmarkConfig, MetricType, NormalizationType


def _load_comparative_template() -> dict:
    template = Path(__file__).resolve().parents[3] / "configs/benchmark_templates/comparative_benchmark_template.json"
    return json.loads(template.read_text(encoding="utf-8"))


def test_from_json_parses_box_plot_with_categorical_metric_defaults():
    cfg = BenchmarkConfig.from_json(_load_comparative_template())

    assert len(cfg.plots) >= 2
    box_plot = next(p for p in cfg.plots if p.plot_type == "box_plot")
    assert box_plot.metric_description == "categorical groups"
    assert box_plot.metric_label == "Algorithm"
    assert box_plot.metric_type == MetricType.ITERATION.value


def test_from_json_parses_max_over_all_normalization_strategy():
    template = _load_comparative_template()
    adapted = deepcopy(template)
    adapted["Benchmark"]["Plot_0"]["PlotType"]["ConvergencePlot"]["ObjectiveAxis"]["NormalizationStrategy"] = {
        "MaxOverAll": {"Type": "max_over_all_experiments"}
    }

    cfg = BenchmarkConfig.from_json(adapted)
    first_plot = cfg.plots[0]
    assert first_plot.normalization_strategy == NormalizationType.MAX_OVER_ALL.value


def test_comparative_analysis_merge_known_optima_with_regret_specific_values():
    template = _load_comparative_template()
    adapted = deepcopy(template)
    adapted["Benchmark"]["KnownOptima"] = {"Y2": 1.23}
    adapted["Benchmark"]["ComparativeAnalysis"]["RegretAnalysis"]["optimumPerObjective"] = {"Y1": 0.0}

    cfg = BenchmarkConfig.from_json(adapted)

    assert cfg.known_optima["Y2"] == 1.23
    assert cfg.comparative_analysis.regret_analysis is not None
    assert cfg.comparative_analysis.regret_analysis.optimum_per_objective == {"Y2": 1.23, "Y1": 0.0}

