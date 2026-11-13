import pandas as pd
from typing import Dict

from configuration_selection.model.candidate_selector.candidate_selector_abs import CandidateSelector

# the number of best-ranked candidates to choose from, see select_candidates
TOP_RANKED = 5


class BestMultiPoint(CandidateSelector):
    def __init__(self, candidate_selector_description: Dict):
        super().__init__(candidate_selector_description)

    def select_candidates(self, candidates: pd.DataFrame) -> pd.DataFrame:
        """
        WORKAROUND: selects randomly among the best-ranked candidates instead of taking the very best ones. Candidates
        are ranked best first, so the best one would be proposed again once it is evaluated. This is a stopgap until
        evaluated configurations are skipped where the regions' predictions are merged.
        :param candidates: candidates ranked best first.
        :return: the selected candidates, indexed from 0.
        """
        top_ranked = candidates.head(max(TOP_RANKED, self.number_of_points))
        selected_candidates = top_ranked.sample(n=min(self.number_of_points, len(top_ranked)))
        return selected_candidates.reset_index(drop=True)
