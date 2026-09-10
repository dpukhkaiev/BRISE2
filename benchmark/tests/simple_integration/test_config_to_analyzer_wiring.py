import json
from pathlib import Path

from analyzer.config import BenchmarkConfig
from analyzer.orchestration.benchmark_analyzer import BenchmarkAnalyzer


def test_comparative_template_wires_comparative_orchestrator():
    template = Path(__file__).resolve().parents[2] / "configs/benchmark_templates/comparative_benchmark_template.json"
    cfg_dict = json.loads(template.read_text(encoding="utf-8"))
    cfg = BenchmarkConfig.from_json(cfg_dict)

    analyzer = BenchmarkAnalyzer(cfg)

    assert analyzer.comparative_orchestrator is not None
    assert cfg.comparative_analysis.is_active() is True


