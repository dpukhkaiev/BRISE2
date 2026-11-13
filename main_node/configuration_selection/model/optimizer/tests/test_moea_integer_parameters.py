import pandas as pd

from configuration_selection.model.optimizer.moea import MOEA
from configuration_selection.model.surrogate.sklearn_wrapper import SklearnWrapper
from core_entities.objectives import Objectives

I1 = "Context.SearchSpace.N0.N02.I1"  # integer [10, 1000]


class TestMoeaProposesIntegers:

    def test_integer_parameter_is_decoded_to_an_integer_by_the_transformer_of_moea(self, get_experiment):
        # 'test_case_13': flat, MOEA with an Integer transformer
        description, search_space = get_experiment(13)
        model = description["ConfigurationSelection"]["Predictor"]["Model"]
        objectives = Objectives.from_description(description["Context"]["TaskConfiguration"]["Objectives"])
        region = search_space.regions[0]
        surrogate = SklearnWrapper(model["Surrogate"], region, objectives)
        optimizer = MOEA(model["Optimizer"], region, objectives)
        optimizer._build_bounds_params_masked(surrogate)
        column = next(c for c in optimizer.params if c.startswith(I1 + "_"))
        proposals = pd.DataFrame([[0.0 if c != column else 0.5 for c in optimizer.params]], columns=optimizer.params)

        decoded = optimizer._inverse_transform_configuration(proposals)

        assert decoded[I1].tolist() == [505]  # 10 + int(0.5 * (1000 - 10 + 1))
        assert all(isinstance(value, int) for value in decoded[I1])
