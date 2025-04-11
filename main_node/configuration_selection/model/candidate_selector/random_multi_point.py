import pandas as pd
from typing import Dict

from configuration_selection.model.candidate_selector.candidate_selector_abs import CandidateSelector


class RandomMultiPoint(CandidateSelector):
    def __init__(self, candidate_selector_description: Dict):
        super().__init__(candidate_selector_description)

    def select_candidates(self, candidates: pd.DataFrame) -> pd.DataFrame:
        candidates = candidates.sample(frac=1).reset_index(drop=True)
        selected_candidates = candidates.head(self.number_of_points)
        return selected_candidates
