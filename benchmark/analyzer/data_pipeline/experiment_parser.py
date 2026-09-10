import re
from typing import Any, Dict


class ExperimentParser:
    """Parses experiment naming and extracts features"""

    PATTERN_WITH_TEST_CASE = re.compile(
        r'^exp_([^_]+)_([^_]+)_([^_]+)_([^_]+)_([^_]+)_test_case_(\d+)(?:_(.+?))?(?:_(\d+))?$')
    PATTERN_BASELINE = re.compile(
        r'^exp_([^_]+)_([^_]+)_([^_]+)_([^_]+)_([^_]+)_baseline_([^_]+(?:-[^_]+)*)(?:_(\d+))?$'
    )
    PATTERN_WITHOUT_TEST_CASE = re.compile(r'^exp_([^_]+)_([^_]+)_([^_]+)_([^_]+)_([^_]+?)(?:_(\d+))?$')
    TEST_CASE_PATTERN = re.compile(r'(test_case_\d+(?:_[a-zA-Z_]+)?)')
    BASELINE_SUFFIX_PATTERN = re.compile(r'_baseline_([^_]+(?:-[^_]+)*)(?:_\d+)?$')
    BASELINE_PREFIX_PATTERN = re.compile(r'^baseline_([^_]+(?:-[^_]+)*)$')

    @staticmethod
    def _empty_features() -> Dict[str, Any]:
        return {
            'Task': None,
            'Model': None,
            'Sampler': None,
            'ConfigurationStrategy': None,
            'StopCondition': None,
            'TestCase': None,
            'Index': None,
            'ExperimentName': None,
        }

    @staticmethod
    def get_name(exp: Any) -> str:
        """Get experiment name or ID"""
        return getattr(exp, 'name', None) or getattr(exp, 'ed_id', None) or 'experiment'

    @staticmethod
    def _is_placeholder_strategy(value: Any) -> bool:
        """Detect placeholder tags produced by generic name builders."""
        if value is None:
            return True
        text = str(value).strip().lower()
        return text in {'', 'none', 'null', 'configstrategy'}

    def parse_features(self, raw_name: str) -> Dict[str, Any]:
        """Parse features from experiment naming pattern

        Expected patterns:
        - exp_<task>_<model>_<sampler>_<configStrategy>_<stopCondition>_test_case_<N>[_<descriptor>][_<idx>]
        - exp_<task>_<model>_<sampler>_<configStrategy>_<stopCondition>[_<idx>]
        """
        features = self._empty_features()

        match = self.PATTERN_WITH_TEST_CASE.match(raw_name)
        if match:
            features['Task'] = match.group(1)
            features['Model'] = match.group(2)
            features['Sampler'] = match.group(3)
            features['ConfigurationStrategy'] = match.group(4)
            features['StopCondition'] = match.group(5)
            features['TestCase'] = int(match.group(6))

            middle_part = match.group(7)
            last_part = match.group(8)

            if middle_part and last_part:
                features['Index'] = int(last_part)
            elif last_part and not middle_part:
                features['Index'] = int(last_part)
            elif middle_part and not last_part and middle_part.isdigit():
                features['Index'] = int(middle_part)

            return features

        match = self.PATTERN_BASELINE.match(raw_name)
        if match:
            features['Task'] = match.group(1)
            features['Model'] = match.group(2)
            features['Sampler'] = match.group(3)
            features['ConfigurationStrategy'] = match.group(4)
            features['StopCondition'] = match.group(5)
            if match.group(7):
                features['Index'] = int(match.group(7))
            return features

        match = self.PATTERN_WITHOUT_TEST_CASE.match(raw_name)
        if match:
            features['Task'] = match.group(1)
            features['Model'] = match.group(2)
            features['Sampler'] = match.group(3)
            features['ConfigurationStrategy'] = match.group(4)
            features['StopCondition'] = match.group(5)
            if match.group(6):
                features['Index'] = int(match.group(6))

        return features

    def parse_features_from_experiment(self, exp: Any) -> Dict[str, Any]:
        """Extract table features from structured metadata with filename fallback."""
        raw_name = self.get_name(exp)
        fallback = self.parse_features(raw_name)
        features = self._empty_features()

        try:
            from analyzer.data_pipeline.experiment_metadata import ExperimentMetadata
            meta = ExperimentMetadata.extract(exp)
        except (ImportError, AttributeError, TypeError, ValueError):
            meta = {}

        model_types = meta.get('model_types') if isinstance(meta.get('model_types'), list) else []
        features['Task'] = meta.get('task_name') or fallback.get('Task')
        features['Model'] = (model_types[0] if model_types else None) or fallback.get('Model')
        features['Sampler'] = (
            meta.get('description.Sampler')
            or meta.get('description.Searchspace.sampler')
            or fallback.get('Sampler')
        )
        # Keep the semantic meaning of "ConfigurationStrategy" aligned with
        # the experiment naming token whenever it is explicitly available.
        name_strategy = fallback.get('ConfigurationStrategy')
        if not self._is_placeholder_strategy(name_strategy):
            features['ConfigurationStrategy'] = name_strategy
        else:
            features['ConfigurationStrategy'] = (
                meta.get('hyperparams_mode')
                or meta.get('tuning_variant')
            )
        features['StopCondition'] = (
            meta.get('description.StopCondition.Name')
            or meta.get('description.StopCondition.Type')
            or fallback.get('StopCondition')
        )
        features['TestCase'] = self._extract_test_case(meta, fallback, raw_name)
        features['Index'] = fallback.get('Index')
        features['ExperimentName'] = raw_name

        return features

    def _extract_test_case(self, meta: Dict[str, Any], fallback: Dict[str, Any], raw_name: str) -> Any:
        if fallback.get('TestCase') is not None:
            return fallback.get('TestCase')

        configured_case = meta.get('description.TaskConfiguration.Scenario.TestCase')
        if configured_case is not None:
            return configured_case

        display_name = self.build_display_name(raw_name)
        match = re.search(r'test_case_(\d+)', display_name)
        if match:
            return int(match.group(1))

        return None

    def build_display_name(self, raw_name: str) -> str:
        """Build display name from raw experiment name

        Examples:
        - exp_test_gpr_sobol_quantitybased_timebased_test_case_0 -> test_case_0
        - exp_test_gpr_sobol_quantitybased_timebased_test_case_2_wo_dch_2 -> test_case_2_wo_dch
        """
        if not raw_name:
            return raw_name

        match = self.TEST_CASE_PATTERN.search(raw_name)
        if match:
            return match.group(1)

        match = self.BASELINE_SUFFIX_PATTERN.search(raw_name)
        if match:
            return match.group(1)

        match = self.BASELINE_PREFIX_PATTERN.match(raw_name)
        if match:
            return match.group(1)

        return raw_name
