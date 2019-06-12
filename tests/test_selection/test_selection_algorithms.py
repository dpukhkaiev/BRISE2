from selection.selection_algorithms import get_selector
from selection.sobol import *
import pytest


def test_get_selector():
    search_space = []
    selection_algorithm_config = {
        "SelectionType": "SobolSequence"
    }
    assert isinstance(get_selector(selection_algorithm_config, search_space), SobolSequence)


def test_get_selector_errors():
    selection_algorithm_config = {}
    search_space = []
    with pytest.raises(KeyError):
        get_selector(selection_algorithm_config, search_space)

    selection_algorithm_config = {
        "SelectionType": 123
    }
    with pytest.raises(KeyError):
        get_selector(selection_algorithm_config, search_space)

    selection_algorithm_config = {
        "SelectionType": "not SobolSequence"
    }
    with pytest.raises(KeyError):
        get_selector(selection_algorithm_config, search_space)
