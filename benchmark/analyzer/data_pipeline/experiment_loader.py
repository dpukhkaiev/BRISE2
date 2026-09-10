import os
import pickle
import re
from typing import List, Any, Dict, Generator

# Apply Cython __pyx_unpickle_* shims for old ConfigSpace pickles before any load
from analyzer.util.legacy_pickle_compat import apply as _apply_legacy_compat

_apply_legacy_compat()

class ExperimentLoader:
    """Loads and groups serialized experiment files"""

    REPETITION_PATTERN = re.compile(r'_(\d+)$')
    LEGACY_DUPLICATE_PATTERN = re.compile(r'(\(\d+\))+$')

    def __init__(self, folder: str):
        self.folder = folder

    def load_all_experiments(self) -> List[Any]:
        experiments: List[Any] = []
        for batch in self.iter_experiment_batches():
            experiments.extend(batch)
        return self._sort_by_start_time(experiments)

    def iter_experiment_batches(self, batch_size: int = 50) -> Generator[List[Any], None, None]:
        pkl_files = self._get_pkl_files()
        if not pkl_files:
            raise FileNotFoundError(f"No .pkl files found in {self.folder}")
        batch: List[Any] = []
        for filename in pkl_files:
            batch.append(self._load_experiment(filename))
            if len(batch) >= batch_size:
                yield self._sort_by_start_time(batch)
                batch = []
        if batch:
            yield self._sort_by_start_time(batch)

    def _get_pkl_files(self) -> List[str]:
        return sorted(f for f in os.listdir(self.folder) if f.endswith('.pkl'))

    def _load_experiment(self, filename: str) -> Any:
        filepath = os.path.join(self.folder, filename)
        with open(filepath, 'rb') as f:
            exp = pickle.load(f)
        exp._source_filename = filename
        return exp

    def _sort_by_start_time(self, experiments: List[Any]) -> List[Any]:
        try:
            return sorted(experiments, key=lambda e: getattr(e, 'start_time', 0))
        except Exception:
            return experiments

    def group_experiments(self, experiments: List[Any]) -> Dict[str, List[Any]]:
        """Group experiments by base name without repetition index.

        Handles two naming conventions:
        - New style: ``exp_task_..._0``, ``exp_task_..._2``  (trailing _N)
        - Legacy style: ``exp_tsp_hh_<hash>(0)``, ``exp_tsp_hh_<hash>(0)(1)`` (trailing (N)...)
        """
        groups: Dict[str, List[Any]] = {}
        for exp in experiments:
            name = self._get_experiment_name(exp)
            base_name = self._remove_repetition_suffix(name)
            groups.setdefault(base_name, []).append(exp)
        return groups

    def _get_experiment_name(self, exp: Any) -> str:
        fname = getattr(exp, '_source_filename', None)
        if fname and fname.endswith('.pkl'):
            return fname[:-4]
        return getattr(exp, 'name', None) or getattr(exp, 'ed_id', None) or 'experiment'

    def _remove_repetition_suffix(self, name: str) -> str:
        """Remove trailing _N or (N)(M)... where N, M are integers"""
        stripped = self.LEGACY_DUPLICATE_PATTERN.sub('', name)
        if stripped != name:
            return stripped
        return self.REPETITION_PATTERN.sub('', name)
