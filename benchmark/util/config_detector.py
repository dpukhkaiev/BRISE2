import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Iterable

logger = logging.getLogger(__name__)


class ConfigDetector:
    """Detects configuration type and available configuration files"""

    DEFAULT_CONFIG_CANDIDATES = [
        "configs/benchmark_templates/configuration.json",
        "configs/benchmark_templates/comparative_benchmark_template.json",
        "configs/benchmark_templates/benchmark_template_with_grouped_testcases.json",
    ]

    @staticmethod
    def detect_config_file(base_dir: Optional[Path] = None,
                           candidates: Optional[Iterable[str]] = None) -> Optional[str]:
        """
        Detect which configuration file to use.

        Returns:
            Path to the configuration file to use, or None if none found
        """
        root = Path(base_dir) if base_dir else Path(__file__).resolve().parents[1]
        selected_candidates = list(candidates) if candidates is not None else ConfigDetector.DEFAULT_CONFIG_CANDIDATES

        for rel_or_abs_path in selected_candidates:
            candidate = Path(rel_or_abs_path)
            resolved = candidate if candidate.is_absolute() else (root / candidate)
            if resolved.exists():
                logger.info(f"Found configuration file: {resolved}")
                return str(resolved)

        logger.warning(f"No configuration file found in configured locations under {root}")
        return None

    @staticmethod
    def load_config(config_path: str) -> Optional[Dict[str, Any]]:
        """
        Load configuration from JSON file.

        Args:
            config_path: Path to configuration file

        Returns:
            Dictionary containing configuration, or None if load failed
        """
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {config_path}: {e}")
        except Exception as e:
            logger.error(f"Error loading {config_path}: {e}")
        return None

    @staticmethod
    def has_comparative_analysis(config_dict: Dict[str, Any]) -> bool:
        """
        Check if configuration includes comparative metrics.

        Args:
            config_dict: Configuration dictionary

        Returns:
            True if comparative metrics are configured
        """
        comp_analysis = config_dict.get("Benchmark", {}).get("ComparativeAnalysis", {})
        if not comp_analysis:
            return False
        enabled = [
            m for m in ["RegretAnalysis", "RelativeImprovement", "PerformanceProfile", "ComparativeTable"]
            if comp_analysis.get(m) and isinstance(comp_analysis[m], dict)
        ]
        if enabled:
            logger.info(f"Comparative analysis detected: {', '.join(enabled)}")
        return bool(enabled)
