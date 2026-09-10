import json
from pathlib import Path

from util.config_detector import ConfigDetector


def test_detect_config_file_prefers_existing_candidate(tmp_path):
    config_path = tmp_path / "picked.json"
    config_path.write_text("{}", encoding="utf-8")

    detected = ConfigDetector.detect_config_file(
        base_dir=tmp_path,
        candidates=["missing.json", "picked.json"],
    )

    assert detected == str(config_path)


def test_load_config_returns_none_on_invalid_json(tmp_path):
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{invalid", encoding="utf-8")

    loaded = ConfigDetector.load_config(str(invalid))

    assert loaded is None


def test_has_comparative_analysis_detects_enabled_sections():
    config = {
        "Benchmark": {
            "ComparativeAnalysis": {
                "RegretAnalysis": {"regretType": ["iteration"]},
                "ComparativeTable": {},
            }
        }
    }

    assert ConfigDetector.has_comparative_analysis(config) is True


def test_has_comparative_analysis_returns_false_without_sections():
    config = {"Benchmark": {"ComparativeAnalysis": {"RegretAnalysis": None}}}

    assert ConfigDetector.has_comparative_analysis(config) is False

