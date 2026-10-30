import pandas as pd

from configuration_selection.model.candidate_selector.best_multi_point import BestMultiPoint, TOP_RANKED


def _selector(number_of_points):
    return BestMultiPoint({"BestMultiPointProposal": {"Type": "best_multi_point", "NumberOfPoints": number_of_points}})


def _ranked(size):
    return pd.DataFrame({"x": range(size), "Y1": [i / size for i in range(size)]})


class TestBestMultiPoint:

    def test_the_selected_candidates_are_indexed_from_zero(self):
        # the predictor merges the partial configurations of regions by their row index
        selected = _selector(3).select_candidates(_ranked(20))

        assert list(selected.index) == [0, 1, 2]


class TestBestMultiPointWorkaround:
    """
    The tests for the top-n reshuffle workaround
    """

    def test_a_candidate_is_chosen_only_among_the_top_ranked_ones(self):
        selector = _selector(1)
        candidates = _ranked(50)

        chosen = {int(selector.select_candidates(candidates)["x"].iloc[0]) for _ in range(300)}

        assert chosen <= set(range(TOP_RANKED))
        assert len(chosen) > 1

    def test_the_requested_number_of_distinct_candidates_is_returned_even_above_the_top_ranked_count(self):
        selected = _selector(8).select_candidates(_ranked(20))

        assert len(selected) == 8
        assert selected["x"].is_unique
        assert set(selected["x"]) <= set(range(8))

    def test_fewer_candidates_than_requested_are_all_returned(self):
        selected = _selector(3).select_candidates(_ranked(2))

        assert sorted(selected["x"]) == [0, 1]
