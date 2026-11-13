import copy

import numpy as np
import pandas as pd
import pytest

from configuration_selection.model.configuration_transformation import build_transformers, write_inactive_values
from configuration_selection.model.optimizer.moea import MOEA
from configuration_selection.model.surrogate.model_mock import ModelMock
from configuration_selection.model.surrogate.sklearn_wrapper import SklearnWrapper
from core_entities.objectives import Objectives
from core_entities.search_space import find_parameters_activated_within_region

N0 = "Context.SearchSpace.N0"
F1 = f"{N0}.N01.F1"  # float [0, 123], active in branch N01
N1 = f"{N0}.N01.N1"  # nominal, two categories, active in branch N01
I1 = f"{N0}.N02.I1"  # integer [10, 1000], active in branch N02
O1 = f"{N0}.N02.O1"  # ordinal, two categories, active in branch N02

# the two ways to transform a nominal parameter; 'test_case_13' uses the binary code
NOMINAL_OPTIONS = {
    "binary_code": None,
    "index": {"SklearnBinaryEncoder": {"Type": "sklearn_binary_transformer", "Class": "sklearn.OrdinalEncoder"}},
}


def _shortened(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.rename(columns=lambda column: column.replace("Context.SearchSpace.", ""))


@pytest.fixture(params=NOMINAL_OPTIONS)
def flat_setup(request, get_experiment):
    """
    'test_case_13' is flat and gives its surrogate and its optimizer the same transformers for the four parameter types.
    The fixture runs once with the nominal transformer of the test case (the binary code) and once with the index.
    """
    description, search_space = get_experiment(13)
    model = copy.deepcopy(description["ConfigurationSelection"]["Predictor"]["Model"])
    if NOMINAL_OPTIONS[request.param]:
        for role in ("Surrogate", "Optimizer"):
            model[role]["ConfigurationTransformers"]["NominalTransformer"] = NOMINAL_OPTIONS[request.param]
    objectives = Objectives.from_description(description["Context"]["TaskConfiguration"]["Objectives"])
    region = search_space.regions[0]
    return SklearnWrapper(model["Surrogate"], region, objectives), MOEA(model["Optimizer"], region, objectives), request.param


@pytest.fixture(params=["float_first", "nominal_first"])
def hierarchical_setup(request, get_experiment):
    """
    'test_case_11' is hierarchical; its second region holds F1 and N1, and its surrogate has only an ordinal and a
    nominal transformer, so F1 has none. The optimizer gets the surrogate's transformers. The fixture runs with the
    parameters of the region in both orders, since a column without a transformer is handled differently when it
    follows a transformed one.
    """
    description, search_space = get_experiment(11)
    model = copy.deepcopy(description["ConfigurationSelection"]["Predictor"]["Model_1"])
    model["Optimizer"]["ConfigurationTransformers"] = copy.deepcopy(model["Surrogate"]["ConfigurationTransformers"])
    objectives = Objectives.from_description(description["Context"]["TaskConfiguration"]["Objectives"])
    region = search_space.regions[1]
    if request.param == "nominal_first":
        region = tuple(reversed(region))
    return SklearnWrapper(model["Surrogate"], region, objectives), MOEA(model["Optimizer"], region, objectives)


def _candidates() -> pd.DataFrame:
    """
    The columns of a flat region, in the order of its parameters. The first row is a candidate of the branch N01, the
    second one of the branch N02; the parameters of the other branch are missing, as in a measured configuration.
    """
    return pd.DataFrame([
        {F1: 61.5, N1: f"{N1}.N12", I1: np.nan, O1: np.nan, N0: f"{N0}.N01"},
        {F1: np.nan, N1: np.nan, I1: 505, O1: f"{O1}.O12", N0: f"{N0}.N02"},
    ])


def _proposals() -> pd.DataFrame:
    """The candidates as the optimizer holds them: a value for every parameter."""
    return pd.DataFrame([
        {F1: 61.5, N1: f"{N1}.N12", I1: 10, O1: f"{O1}.O11", N0: f"{N0}.N01"},
        {F1: 0.0, N1: f"{N1}.N11", I1: 505, O1: f"{O1}.O12", N0: f"{N0}.N02"},
    ])


class TestTransformersBuiltForARegion:

    def test_each_transformer_serves_the_parameters_of_its_type(self, flat_setup):
        surrogate, optimizer, _ = flat_setup

        for consumer in (surrogate, optimizer):
            names_by_type = {}
            for parameters in consumer.mapping_config_transformer_parameter.values():
                parameter_type = parameters[0].type  # a transformer serves the parameters of one type
                names_by_type[parameter_type] = [hp.name for hp in parameters]

            assert names_by_type == {"Float": [F1], "Nominal": [N1, N0], "Integer": [I1], "Ordinal": [O1]}

    def test_only_the_transformers_of_the_surrogate_know_the_inactive_value_of_the_parameters_that_can_be_inactive(
            self, flat_setup):
        surrogate, optimizer, _ = flat_setup

        for transformer in surrogate.mapping_config_transformer_parameter:
            assert transformer.parameters_with_inactive_value == frozenset({F1, N1, I1, O1})
        for transformer in optimizer.mapping_config_transformer_parameter:
            assert transformer.parameters_with_inactive_value == frozenset()


class TestTransformationOfAFlatRegion:

    def test_surrogate_transforms_every_parameter_with_the_inactive_value_where_the_parameter_is_missing(self, flat_setup):
        surrogate, _, nominal_option = flat_setup

        transformed = _shortened(surrogate._transform_configuration(_candidates()))

        if nominal_option == "binary_code":
            # the inactive value is a third category of N1, so its code takes two bits
            expected = pd.DataFrame(
                [[0.5, 0, 1, -1.0, 2.0, 0],
                 [-1.0, 1, 0, 0.5, 1.0, 1]],
                columns=["N0.N01.F1_MinMaxScaler", "N0.N01.N1_BinaryEncoder0", "N0.N01.N1_BinaryEncoder1",
                         "N0.N02.I1_MinMaxScaler", "N0.N02.O1_OrdinalEncoder", "N0_BinaryEncoder"])
        else:
            expected = pd.DataFrame(
                [[0.5, 1.0, -1.0, 2.0, 0.0],
                 [-1.0, 2.0, 0.5, 1.0, 1.0]],
                columns=["N0.N01.F1_MinMaxScaler", "N0.N01.N1_OrdinalEncoder", "N0.N02.I1_MinMaxScaler",
                         "N0.N02.O1_OrdinalEncoder", "N0_OrdinalEncoder"])
        pd.testing.assert_frame_equal(transformed, expected, check_dtype=False)

    def test_optimizer_transforms_every_parameter_without_an_inactive_value(self, flat_setup):
        _, optimizer, nominal_option = flat_setup

        transformed = _shortened(optimizer._transform_configuration(_proposals()))

        if nominal_option == "binary_code":
            expected = pd.DataFrame(
                [[0.5, 1, 0.0, 0.0, 0],
                 [0.0, 0, 0.5, 1.0, 1]],
                columns=["N0.N01.F1_MinMaxScaler", "N0.N01.N1_BinaryEncoder", "N0.N02.I1_MinMaxScaler",
                         "N0.N02.O1_OrdinalEncoder", "N0_BinaryEncoder"])
        else:
            expected = pd.DataFrame(
                [[0.5, 1.0, 0.0, 0.0, 0.0],
                 [0.0, 0.0, 0.5, 1.0, 1.0]],
                columns=["N0.N01.F1_MinMaxScaler", "N0.N01.N1_OrdinalEncoder", "N0.N02.I1_MinMaxScaler",
                         "N0.N02.O1_OrdinalEncoder", "N0_OrdinalEncoder"])
        pd.testing.assert_frame_equal(transformed, expected, check_dtype=False)

    def test_a_proposal_is_transformed_as_it_is_inside_a_batch(self, flat_setup):
        _, optimizer, _ = flat_setup
        proposals = _proposals()

        batch = optimizer._transform_configuration(proposals)

        for i in range(len(proposals)):
            alone = optimizer._transform_configuration(proposals.iloc[[i]])
            pd.testing.assert_frame_equal(batch.iloc[[i]].reset_index(drop=True), alone)

    def test_rows_are_transformed_by_position_whatever_their_index(self, flat_setup):
        surrogate, _, _ = flat_setup
        rows = _candidates()

        shifted = surrogate._transform_configuration(rows.set_axis([7, 3]))

        pd.testing.assert_frame_equal(shifted, surrogate._transform_configuration(rows))

    def test_a_surrogate_without_transformers_still_gets_the_inactive_value_in_the_cells_of_inactive_parameters(
            self, get_experiment):
        description, search_space = get_experiment(13)
        region = search_space.regions[0]
        objectives = Objectives.from_description(description["Context"]["TaskConfiguration"]["Objectives"])
        surrogate = ModelMock({"Instance": {"ModelMock": {"MultiObjective": False}}}, region, objectives)
        inactive = {hp.name: hp.inactive_value() for hp in region}

        transformed = surrogate._transform_configuration(_candidates())

        expected = pd.DataFrame([
            {F1: 61.5, N1: f"{N1}.N12", I1: inactive[I1], O1: inactive[O1], N0: f"{N0}.N01"},
            {F1: inactive[F1], N1: inactive[N1], I1: 505, O1: f"{O1}.O12", N0: f"{N0}.N02"},
        ])
        pd.testing.assert_frame_equal(transformed, expected, check_dtype=False)

    def test_an_optimizer_without_transformers_leaves_the_features_as_they_are(self, get_experiment):
        description, search_space = get_experiment(13)
        model = copy.deepcopy(description["ConfigurationSelection"]["Predictor"]["Model"])
        del model["Optimizer"]["ConfigurationTransformers"]
        objectives = Objectives.from_description(description["Context"]["TaskConfiguration"]["Objectives"])
        optimizer = MOEA(model["Optimizer"], search_space.regions[0], objectives)

        pd.testing.assert_frame_equal(optimizer._transform_configuration(_proposals()), _proposals())


class TestTransformationOfAHierarchicalRegion:

    def test_a_parameter_without_a_transformer_passes_through(self, hierarchical_setup):
        surrogate, optimizer = hierarchical_setup
        candidates = pd.DataFrame({F1: [123.0, 0.0], N1: [f"{N1}.N12", f"{N1}.N11"]})[[hp.name for hp in surrogate.region]]
        # nothing is written into a hierarchical region; F1 has no Float transformer in this surrogate, so it stays
        expected = pd.DataFrame({"N0.N01.F1": [123.0, 0.0], "N0.N01.N1_BinaryEncoder": [1, 0]})

        for consumer in (surrogate, optimizer):
            transformed = _shortened(consumer._transform_configuration(candidates))
            pd.testing.assert_frame_equal(transformed, expected[list(transformed.columns)], check_dtype=False)


class TestInverseTransformationOfAnOptimizersProposals:

    def test_proposals_of_a_flat_region_are_transformed_back_into_configurations(self, flat_setup):
        _, optimizer, _ = flat_setup
        transformed = optimizer._transform_configuration(_proposals())
        proposals = pd.DataFrame(
            [[0.5, 0.9, 0.5, 0.9, 0.9], [0.0, 0.1, 0.0, 0.1, 0.1]], columns=transformed.columns)

        transformed_back = optimizer._inverse_transform_configuration(proposals)

        expected = pd.DataFrame([
            {F1: 61.5, N1: f"{N1}.N12", I1: 505, O1: f"{O1}.O12", N0: f"{N0}.N02"},
            {F1: 0.0, N1: f"{N1}.N11", I1: 10, O1: f"{O1}.O11", N0: f"{N0}.N01"},
        ])
        pd.testing.assert_frame_equal(transformed_back, expected, check_dtype=False)

    def test_the_transformed_proposals_are_transformed_back_into_the_configurations_they_came_from(self, flat_setup):
        _, optimizer, _ = flat_setup
        proposals = _proposals()

        transformed_back = optimizer._inverse_transform_configuration(optimizer._transform_configuration(proposals))

        pd.testing.assert_frame_equal(transformed_back, proposals, check_dtype=False)

    def test_a_proposal_is_transformed_back_as_it_is_inside_a_batch(self, flat_setup):
        _, optimizer, _ = flat_setup
        transformed = optimizer._transform_configuration(_proposals())

        batch = optimizer._inverse_transform_configuration(transformed)

        for i in range(len(transformed)):
            alone = optimizer._inverse_transform_configuration(transformed.iloc[[i]].reset_index(drop=True))
            pd.testing.assert_frame_equal(batch.iloc[[i]].reset_index(drop=True), alone)

    def test_a_parameter_without_a_transformer_is_returned_as_it_is(self, hierarchical_setup):
        surrogate, optimizer = hierarchical_setup
        # the transformers learn their columns one parameter at a time, as MOEA does when it builds its bounds; the
        # columns of a parameter without a transformer stay unknown to them
        optimizer._build_bounds_params_masked(surrogate)
        proposals = pd.DataFrame([[0.9, 0.9], [0.1, 0.1]], columns=optimizer.params)

        transformed_back = optimizer._inverse_transform_configuration(proposals)

        expected = pd.DataFrame({F1: [0.9, 0.1], N1: [f"{N1}.N12", f"{N1}.N11"]})[[hp.name for hp in optimizer.region]]
        pd.testing.assert_frame_equal(transformed_back, expected, check_dtype=False)


class TestConfigurationTransformationFunctions:

    def test_transformers_know_the_inactive_value_only_of_the_parameters_they_are_told_of(self, get_experiment):
        description, search_space = get_experiment(13)
        optimizer_description = description["ConfigurationSelection"]["Predictor"]["Model"]["Optimizer"]
        region = search_space.regions[0]

        without = build_transformers(optimizer_description, region)
        with_inactive = build_transformers(optimizer_description, region, frozenset({F1, N1}))

        for transformer in without:
            assert transformer.parameters_with_inactive_value == frozenset()
        for transformer in with_inactive:
            assert transformer.parameters_with_inactive_value == frozenset({F1, N1})

    def test_only_the_cells_of_inactive_conditional_parameters_get_the_inactive_value(self, get_experiment):
        _, search_space = get_experiment(13)
        region = search_space.regions[0]
        candidates = _candidates()
        inactive_values = {hp.name: hp.inactive_value() for hp in region}

        written = write_inactive_values(candidates, find_parameters_activated_within_region(region))

        assert written[F1].tolist() == [61.5, inactive_values[F1]]
        assert written[N1].tolist() == [f"{N1}.N12", inactive_values[N1]]
        assert written[I1].tolist() == [inactive_values[I1], 505]
        assert written[O1].tolist() == [inactive_values[O1], f"{O1}.O12"]
        assert written[N0].tolist() == [f"{N0}.N01", f"{N0}.N02"]
        assert candidates[I1].isna().tolist() == [True, False]  # the candidates are not changed

    def test_features_are_returned_as_they_are_without_conditional_parameters(self):
        candidates = _candidates()

        assert write_inactive_values(candidates, []) is candidates
