import pandas as pd
import pytest

from configuration_selection.model.value_transformer.tpe_ei import TpeEi

# rows of (probability_good, probability_bad); the last one has no finite ratio when minimizing
PROBABILITIES = pd.DataFrame({"Y1_probability_good": [0.5, 0.2, 0.0], "Y1_probability_bad": [0.1, 0.4, 0.3]})


def _acquisition_function(minimization):
    return TpeEi({"TPE_EI": {"Type": "tpe_ei"}}, {"Y1": {"Name": "Y1", "Minimization": minimization}})


class TestTpeEi:

    @pytest.mark.parametrize("minimization, expected", [(True, [0.2, 2.0, 0.0]), (False, [5.0, 0.5, 0.0])])
    def test_each_row_of_a_batch_gets_its_own_ratio(self, minimization, expected):
        acquisition_function = _acquisition_function(minimization)

        batch = acquisition_function.transform(PROBABILITIES)["ratio"].tolist()
        rows = [acquisition_function.transform(PROBABILITIES.iloc[[i]].reset_index(drop=True))["ratio"].iloc[0]
                for i in range(len(PROBABILITIES))]

        assert batch == pytest.approx(expected)
        assert rows == pytest.approx(expected)
