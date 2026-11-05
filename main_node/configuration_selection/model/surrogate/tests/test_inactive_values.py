import copy

import numpy as np
import pandas as pd
import pytest

from configuration_selection.model.configuration_transformer.binary_transformer import BinaryTransformer
from configuration_selection.model.optimizer.moea import MOEA
from configuration_selection.model.surrogate.sklearn_wrapper import SklearnWrapper
from core_entities.search_space import NominalHyperparameter, find_parameters_activated_within_region

N0 = "Context.SearchSpace.N0"
N01 = f"{N0}.N01"
N02 = f"{N0}.N02"
F1 = f"{N01}.F1"  # float [0, 123]
N1 = f"{N01}.N1"  # nominal, two categories
I1 = f"{N02}.I1"  # integer [10, 1000]
O1 = f"{N02}.O1"  # ordinal, two categories
N1_CATEGORIES = [f"{N1}.N11", f"{N1}.N12"]
O1_CATEGORIES = [f"{O1}.O11", f"{O1}.O12"]


@pytest.fixture
def flat_setup(get_experiment):
    """
    'test_case_13' is flat, has the branches N01 {F1, N1} and N02 {I1, O1}, and gives its surrogate and its
    optimizer the same transformers for the four parameter types.
    """
    description, search_space = get_experiment(13)
    model = description["ConfigurationSelection"]["Predictor"]["Model"]
    objectives = description["Context"]["TaskConfiguration"]["Objectives"]
    region = search_space.regions[0]
    surrogate = SklearnWrapper(model["Surrogate"], region, objectives)
    optimizer = MOEA(model["Optimizer"], region, objectives)
    return surrogate, optimizer, region


@pytest.fixture
def hierarchical_setup(get_experiment):
    """
    'test_case_11' is hierarchical; its second model serves the regions of the first level and gives its surrogate
    and its optimizer the same transformers.
    """
    description, search_space = get_experiment(11)
    model = description["ConfigurationSelection"]["Predictor"]["Model_1"]
    objectives = description["Context"]["TaskConfiguration"]["Objectives"]
    region = search_space.regions[1]
    return SklearnWrapper(model["Surrogate"], region, objectives), MOEA(model["Optimizer"], region, objectives), region


def _candidate(branch: str, **overrides) -> dict:
    """A candidate carries a value for every parameter, also for the ones its branch doesn't activate."""
    candidate = {N0: branch, F1: 61.5, N1: N1_CATEGORIES[1], I1: 505, O1: O1_CATEGORIES[1]}
    candidate.update(overrides)
    return candidate


def _reduced(candidate: dict, active: list) -> dict:
    return {name: candidate[name] for name in active}


def _columns(encoded: pd.DataFrame, parameter: str) -> list:
    return [c for c in encoded.columns if c.startswith(parameter + "_")]


def _encode(surrogate, rows: list) -> pd.DataFrame:
    return surrogate._transform_configuration(pd.DataFrame(rows).reindex(columns=[N0, F1, N1, I1, O1]))


class TestInactiveValueInTheSurrogateInput:

    @pytest.mark.parametrize("branch, expected", [
        # the inactive value: -1 for a number, the index after the last category for the ordinal, the code after the
        # categories for the nominal; the values of the active branch encode as they are
        (N01, {F1: [61.5 / 123], N1: [0.0, 1.0], I1: [-1.0], O1: [len(O1_CATEGORIES)]}),
        (N02, {F1: [-1.0], N1: [1.0, 0.0], I1: [(505 - 10) / (1000 - 10)], O1: [1.0]}),
    ])
    def test_candidate_gets_the_inactive_value_in_the_columns_of_the_branch_it_doesnt_activate(
            self, flat_setup, branch, expected):
        surrogate, _, _ = flat_setup

        encoded = _encode(surrogate, [_candidate(branch)])

        for parameter, values in expected.items():
            assert list(encoded[_columns(encoded, parameter)].iloc[0]) == pytest.approx(values), parameter

    def test_training_row_without_its_inactive_parameters_encodes_like_the_candidate_with_them(self, flat_setup):
        surrogate, _, _ = flat_setup
        candidate = _candidate(N01)

        from_candidate = _encode(surrogate, [candidate])
        from_training_row = _encode(surrogate, [_reduced(candidate, [N0, F1, N1])])

        pd.testing.assert_frame_equal(from_candidate, from_training_row)

    def test_the_value_does_not_depend_on_what_the_candidate_holds_for_an_inactive_parameter(self, flat_setup):
        surrogate, _, _ = flat_setup

        first = _encode(surrogate, [_candidate(N01, **{I1: 11, O1: O1_CATEGORIES[0]})])
        second = _encode(surrogate, [_candidate(N01, **{I1: 999, O1: O1_CATEGORIES[1]})])

        pd.testing.assert_frame_equal(first, second)

    def test_a_row_encodes_as_it_does_inside_a_batch(self, flat_setup):
        surrogate, _, _ = flat_setup
        rows = [_candidate(N01), _candidate(N02), _reduced(_candidate(N01), [N0, F1, N1])]

        batch = _encode(surrogate, rows)

        for i, row in enumerate(rows):
            alone = _encode(surrogate, [row])
            pd.testing.assert_frame_equal(batch.iloc[[i]].reset_index(drop=True), alone)

    def test_no_real_value_encodes_to_the_inactive_value(self, flat_setup):
        surrogate, _, region = flat_setup
        encodings = {}
        for hp in find_parameters_activated_within_region(region):
            if hasattr(hp, "categories"):
                values = list(hp.categories)
                for value in values:
                    encodings[(hp.name, value)] = _transform_alone(surrogate, hp.name, value)
                assert _transform_alone(surrogate, hp.name, hp.inactive_value()) not in encodings.values()
            else:
                for value in (hp.get_lower(), hp.get_upper()):
                    assert _transform_alone(surrogate, hp.name, value) != _transform_alone(surrogate, hp.name, hp.inactive_value())

    def test_top_level_parameter_is_not_given_the_inactive_value(self, flat_setup):
        surrogate, _, _ = flat_setup

        encoded = _encode(surrogate, [_candidate(N01), _candidate(N02)])

        assert encoded[_columns(encoded, N0)].values.tolist() == [[0], [1]]  # codes 0 and 1 of the two branches


def _transform_alone(surrogate, name: str, value) -> tuple:
    """The encoding of one value of one parameter, as the surrogate's transformers give it."""
    for transformer, parameters in surrogate.mapping_config_transformer_parameter.items():
        if any(hp.name == name for hp in parameters):
            return tuple(transformer.transform(pd.DataFrame({name: [value]})).iloc[0])
    raise AssertionError(f"no transformer for {name}")


class TestBinaryCodeOfAParameterThatCanBeInactive:

    @pytest.mark.parametrize("number_of_categories, bits", [(2, 2), (3, 2), (4, 3), (7, 3), (8, 4)])
    def test_the_code_holds_the_categories_and_the_inactive_value(self, number_of_categories, bits):
        # the inactive value is one more category, so it takes a bit more when the categories fill their bits
        hp = NominalHyperparameter("n", 0, [f"c{i}" for i in range(number_of_categories)])
        transformer = BinaryTransformer({"BinaryEncoder": {"Type": "binary_transformer"}}, (hp,), frozenset({"n"}))

        assert transformer.transform(pd.DataFrame({"n": ["c0"]})).shape[1] == bits

    @pytest.mark.parametrize("number_of_categories", [2, 3, 4, 5, 7, 8])
    def test_the_inactive_value_has_a_code_of_its_own(self, number_of_categories):
        hp = NominalHyperparameter("n", 0, [f"c{i}" for i in range(number_of_categories)])
        transformer = BinaryTransformer({"BinaryEncoder": {"Type": "binary_transformer"}}, (hp,), frozenset({"n"}))

        values = [*hp.categories, hp.inactive_value()]
        codes = {tuple(transformer.transform(pd.DataFrame({"n": [v]})).iloc[0]) for v in values}

        assert len(codes) == number_of_categories + 1


class TestOptimizersKeepTheirDomain:

    def test_optimizer_transformers_know_nothing_of_the_inactive_value(self, flat_setup):
        surrogate, optimizer, _ = flat_setup

        assert all(t.parameters_with_inactive_value for t in surrogate.mapping_config_transformer_parameter)
        assert not any(t.parameters_with_inactive_value for t in optimizer.mapping_config_transformer_parameter)

    def test_search_bounds_of_the_optimizer_stay_inside_the_categories(self, flat_setup):
        surrogate, optimizer, _ = flat_setup

        optimizer._build_bounds_params_masked(surrogate)

        bounds = dict(zip(optimizer.params, zip(*optimizer.bounds)))
        ordinal_column = next(c for c in optimizer.params if c.startswith(O1 + "_"))
        assert bounds[ordinal_column] == (0.0, float(len(O1_CATEGORIES) - 1))

    # TOBEDROPPED
    def test_optimizer_without_its_own_transformer_does_not_borrow_the_one_of_a_parameter_that_can_be_inactive(
            self, flat_setup, get_experiment):
        surrogate, _, region = flat_setup
        description, _ = get_experiment(13)
        model = copy.deepcopy(description["ConfigurationSelection"]["Predictor"]["Model"])
        del model["Optimizer"]["ConfigurationTransformers"]
        optimizer = MOEA(model["Optimizer"], region, description["Context"]["TaskConfiguration"]["Objectives"])

        with pytest.raises(ValueError, match="can be inactive"):
            optimizer._build_bounds_params_masked(surrogate)

    def test_surrogate_encoding_is_not_skipped_in_a_flat_region_even_for_equal_transformers(self, flat_setup):
        surrogate, optimizer, _ = flat_setup

        assert optimizer._resolve_configuration_transformers(surrogate) == (True, True)

    def test_equal_transformers_skip_the_double_transformation_in_a_hierarchical_region(self, hierarchical_setup):
        surrogate, optimizer, _ = hierarchical_setup

        assert optimizer._resolve_configuration_transformers(surrogate) == (False, False)

    def test_hierarchical_features_are_returned_as_they_are(self, hierarchical_setup):
        surrogate, _, region = hierarchical_setup
        features = pd.DataFrame([{hp.name: np.nan for hp in region}])

        assert surrogate._write_inactive_values(features) is features


class TestParametersActivatedWithinRegion:

    def test_every_nested_parameter_of_the_flat_region_is_conditional(self, flat_setup):
        _, _, region = flat_setup

        assert {hp.name for hp in find_parameters_activated_within_region(region)} == {F1, N1, I1, O1}

    def test_no_parameter_of_a_hierarchical_region_is_conditional(self, get_experiment):
        # a parent activates the region of the next level, so it never sits in the region of its children
        _, search_space = get_experiment(11)

        assert [find_parameters_activated_within_region(region) for region in search_space.regions] == [[]] * len(search_space.regions)
