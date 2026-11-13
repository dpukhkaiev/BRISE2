import numpy as np
import pandas as pd
import pytest
from sklearn.exceptions import NotFittedError
from sklearn.preprocessing import MinMaxScaler
from sklearn.utils.validation import check_is_fitted

from core_entities.search_space import (
    FloatHyperparameter,
    IntegerHyperparameter,
    NominalHyperparameter,
    OrdinalHyperparameter,
)
from configuration_selection.model.configuration_transformer.binary_transformer import BinaryTransformer
from configuration_selection.model.configuration_transformer.sklearn_column_encoder import SklearnColumnTransformer
from configuration_selection.model.configuration_transformer.sklearn_binary_transformer import SklearnBinaryTransformer
from configuration_selection.model.configuration_transformer.sklearn_float_transformer import SklearnFloatTransformer
from configuration_selection.model.configuration_transformer.sklearn_integer_transformer import SklearnIntegerTransformer
from configuration_selection.model.configuration_transformer.sklearn_ordinal_transformer import SklearnOrdinalTransformer

FLOAT = FloatHyperparameter("f", 0, 2.0, 6.0)
INTEGER = IntegerHyperparameter("i", 0, 1, 10)
ORDINAL = OrdinalHyperparameter("o", 0, ["a", "b", "c", "d"])
NOMINAL = NominalHyperparameter("n", 0, ["a", "b", "c", "d"])
# five categories take three bits in a binary code, so three of the eight codes are unused
BIT_CODED = NominalHyperparameter("b", 0, ["a", "b", "c", "d", "e"])


# a transformer class, the hyperparameter it serves and three of its values
ONE_PARAMETER = ((SklearnFloatTransformer, FLOAT, [2.0, 3.0, 6.0]), (SklearnIntegerTransformer, INTEGER, [1, 5, 10]),
                      (SklearnOrdinalTransformer, ORDINAL, ["a", "b", "d"]), (SklearnBinaryTransformer, NOMINAL, ["a", "b", "d"]),
                      (BinaryTransformer, BIT_CODED, ["a", "c", "e"]))
ONE_PARAMETER_NAMES = [case[0].__name__ for case in ONE_PARAMETER]


def _transformer(transformer_class, hyperparameter):
    return transformer_class({"Transformer": {"Type": "test"}}, (hyperparameter,))


def _shares(decoded: pd.Series) -> pd.Series:
    return decoded.value_counts(normalize=True).sort_index()


class TestDomainFitting:

    def test_numeric_bounds_encode_to_zero_and_one_in_any_batch(self):
        for transformer_class, hyperparameter in ((SklearnFloatTransformer, FLOAT), (SklearnIntegerTransformer, INTEGER)):
            transformer = _transformer(transformer_class, hyperparameter)
            lower, upper = hyperparameter.get_lower(), hyperparameter.get_upper()

            single_row = transformer.transform(pd.DataFrame({hyperparameter.name: [lower]}))
            other_single_row = transformer.transform(pd.DataFrame({hyperparameter.name: [upper]}))
            batch = transformer.transform(pd.DataFrame({hyperparameter.name: [lower, upper]}))

            assert single_row.iloc[0, 0] == 0.0
            assert other_single_row.iloc[0, 0] == 1.0
            assert batch.iloc[:, 0].tolist() == [0.0, 1.0]

    def test_a_category_encodes_to_its_index_in_any_batch(self):
        for transformer_class, hyperparameter in ((SklearnOrdinalTransformer, ORDINAL), (SklearnBinaryTransformer, NOMINAL)):
            transformer = _transformer(transformer_class, hyperparameter)

            alone = transformer.transform(pd.DataFrame({hyperparameter.name: ["d"]}))
            batch = transformer.transform(pd.DataFrame({hyperparameter.name: ["a", "d"]}))

            assert alone.iloc[0, 0] == 3.0
            assert batch.iloc[:, 0].tolist() == [0.0, 3.0]


class TestFittedState:

    def test_an_adapter_is_unfitted_until_it_is_fitted(self):
        adapter = SklearnColumnTransformer(MinMaxScaler(), input_column_names=["f"])

        with pytest.raises(NotFittedError):
            check_is_fitted(adapter)

        adapter.fit(pd.DataFrame({"f": [2.0, 6.0]}))

        check_is_fitted(adapter)

    @pytest.mark.parametrize("transformer_class, hyperparameter, values", ONE_PARAMETER, ids=ONE_PARAMETER_NAMES)
    def test_every_pipeline_a_transformer_builds_is_fitted(self, transformer_class, hyperparameter, values):
        transformer = _transformer(transformer_class, hyperparameter)

        transformer.transform(pd.DataFrame({hyperparameter.name: [values[0]]}))

        assert len(transformer.mapping_old_feature_pipeline) == 1
        for pipeline in transformer.mapping_old_feature_pipeline.values():
            check_is_fitted(pipeline)

    @pytest.mark.parametrize("transformer_class, hyperparameter, values", ONE_PARAMETER, ids=ONE_PARAMETER_NAMES)
    def test_a_transformer_fits_the_pipeline_of_a_parameter_only_once(self, monkeypatch, transformer_class,
                                                                      hyperparameter, values):
        fits = []
        fit = SklearnColumnTransformer.fit

        def counting_fit(adapter, *args, **kwargs):
            fits.append(adapter.input_column_names)
            return fit(adapter, *args, **kwargs)

        monkeypatch.setattr(SklearnColumnTransformer, "fit", counting_fit)
        transformer = _transformer(transformer_class, hyperparameter)

        for value in values:
            transformer.transform(pd.DataFrame({hyperparameter.name: [value]}))

        assert fits == [[hyperparameter.name]]


class TestRowAlignment:

    @pytest.mark.parametrize("transformer_class, hyperparameter, values", ONE_PARAMETER, ids=ONE_PARAMETER_NAMES)
    def test_rows_are_transformed_by_position_whatever_their_index(self, transformer_class, hyperparameter, values):
        transformer = _transformer(transformer_class, hyperparameter)
        one_row_each = [transformer.transform(pd.DataFrame({hyperparameter.name: [value]})) for value in values]
        features = pd.DataFrame({hyperparameter.name: values, "other": [10, 20, 30]}, index=[7, 2, 5])

        transformed = transformer.transform(features)

        pd.testing.assert_frame_equal(transformed.drop(columns="other"), pd.concat(one_row_each, ignore_index=True))
        assert transformed["other"].tolist() == [10, 20, 30]


class TestEqualWidthDecoding:
    """
    Some Optimizers (e.g. MOEA) propose continuous values, so every category and every integer must get an equal share
    of the range they are drawn from, including the first and the last one.
    """

    @staticmethod
    def _decode(transformer, hyperparameter, any_valid_value, encoded_values):
        # a transformer knows its pipelines and encoded column names only after its first transform()
        encoded_name = transformer.transform(pd.DataFrame({hyperparameter.name: [any_valid_value]})).columns[0]
        return transformer.inverse_transform(pd.DataFrame({encoded_name: encoded_values}))[hyperparameter.name]

    def test_ordinal_categories_get_equal_shares_of_the_encoded_range(self):
        transformer = _transformer(SklearnOrdinalTransformer, ORDINAL)

        decoded = self._decode(transformer, ORDINAL, "a", np.linspace(0, 3, 4000))

        assert list(_shares(decoded).index) == ["a", "b", "c", "d"]
        assert np.allclose(_shares(decoded).values, 0.25, atol=0.01)

    def test_nominal_categories_get_equal_shares_of_the_encoded_range(self):
        transformer = _transformer(SklearnBinaryTransformer, NOMINAL)

        decoded = self._decode(transformer, NOMINAL, "a", np.linspace(0, 3, 4000))

        assert list(_shares(decoded).index) == ["a", "b", "c", "d"]
        assert np.allclose(_shares(decoded).values, 0.25, atol=0.01)

    def test_decoding_an_exact_category_index_returns_that_category(self):
        for transformer_class, hyperparameter in ((SklearnOrdinalTransformer, ORDINAL), (SklearnBinaryTransformer, NOMINAL)):
            transformer = _transformer(transformer_class, hyperparameter)

            decoded = self._decode(transformer, hyperparameter, "a", [0.0, 1.0, 2.0, 3.0])

            assert decoded.tolist() == ["a", "b", "c", "d"]

    def test_a_single_category_is_always_decoded_to_itself(self):
        hyperparameter = NominalHyperparameter("n", 0, ["only"])
        transformer = _transformer(SklearnBinaryTransformer, hyperparameter)

        decoded = self._decode(transformer, hyperparameter, "only", [0.0, 0.4, 1.0])

        assert decoded.tolist() == ["only"] * 3

    def test_integers_get_equal_shares_of_the_encoded_range(self):
        transformer = _transformer(SklearnIntegerTransformer, INTEGER)

        decoded = self._decode(transformer, INTEGER, 1, np.linspace(0, 1, 10000))

        assert list(_shares(decoded).index) == list(range(1, 11))
        assert np.allclose(_shares(decoded).values, 0.1, atol=0.01)

    def test_the_ends_of_the_encoded_range_decode_to_the_integer_bounds(self):
        transformer = _transformer(SklearnIntegerTransformer, INTEGER)

        decoded = self._decode(transformer, INTEGER, 1, [0.0, 1.0])

        assert decoded.tolist() == [1, 10]

    def test_floats_decode_linearly_between_their_bounds(self):
        transformer = _transformer(SklearnFloatTransformer, FLOAT)

        decoded = self._decode(transformer, FLOAT, 2.0, [0.0, 0.25, 1.0])

        assert decoded.tolist() == [2.0, 3.0, 6.0]


class TestBinaryCode:
    """
    BinaryTransformer encodes a nominal parameter as the binary code of its category's index, one column per bit.
    """

    @pytest.mark.parametrize("number_of_categories, bits", [(2, 1), (3, 2), (4, 2), (5, 3), (8, 3), (9, 4)])
    def test_the_code_has_the_fewest_bits_that_hold_the_highest_index(self, number_of_categories, bits):
        hyperparameter = NominalHyperparameter("n", 0, [f"c{i}" for i in range(number_of_categories)])
        transformer = _transformer(BinaryTransformer, hyperparameter)

        codes = transformer.transform(pd.DataFrame({"n": list(hyperparameter.categories)}))

        assert codes.shape[1] == bits
        assert len({tuple(code) for code in codes.values.tolist()}) == number_of_categories

    def test_a_category_encodes_to_the_binary_code_of_its_index_in_any_batch(self):
        transformer = _transformer(BinaryTransformer, BIT_CODED)

        alone = transformer.transform(pd.DataFrame({"b": ["c"]}))
        batch = transformer.transform(pd.DataFrame({"b": ["a", "c", "e"]}))

        assert alone.values.tolist() == [[0, 1, 0]]
        assert batch.values.tolist() == [[0, 0, 0], [0, 1, 0], [1, 0, 0]]

    def test_decoding_an_exact_code_returns_its_category(self):
        transformer = _transformer(BinaryTransformer, BIT_CODED)
        encoded = transformer.transform(pd.DataFrame({"b": BIT_CODED.categories})).astype(float)

        assert transformer.inverse_transform(encoded)["b"].tolist() == list(BIT_CODED.categories)

    def test_a_continuous_bit_vector_decodes_to_the_category_with_the_nearest_code(self):
        """
        A vector that is not a valid code is decoded to the nearest valid one. 
        Thus, categories get unequal shares.
        """
        transformer = _transformer(BinaryTransformer, BIT_CODED)
        columns = transformer.transform(pd.DataFrame({"b": ["a"]})).columns
        proposals = pd.DataFrame([[0.1, 0.2, 0.1], [0.9, 0.9, 0.9], [0.9, 0.1, 0.4]], columns=columns)

        # nearest codes: 000 (a); 011 (d), as the unused code 111 is not valid; 100 (e)
        assert transformer.inverse_transform(proposals)["b"].tolist() == ["a", "d", "e"]


TWO_PARAMETERS = [
    (SklearnFloatTransformer, FloatHyperparameter("f1", 0, 2.0, 6.0), FloatHyperparameter("f2", 0, 0.0, 1.0),
     [2.0, 4.0, 6.0], [0.0, 0.5, 1.0]),
    (SklearnIntegerTransformer, IntegerHyperparameter("i1", 0, 1, 10), IntegerHyperparameter("i2", 0, 0, 4),
     [1, 5, 10], [0, 2, 4]),
    (SklearnOrdinalTransformer, OrdinalHyperparameter("o1", 0, ["a", "b", "c"]),
     OrdinalHyperparameter("o2", 0, ["x", "y", "z"]), ["a", "b", "c"], ["z", "y", "x"]),
    (SklearnBinaryTransformer, NominalHyperparameter("n1", 0, ["a", "b", "c"]),
     NominalHyperparameter("n2", 0, ["x", "y", "z"]), ["a", "b", "c"], ["z", "y", "x"]),
    (BinaryTransformer, NominalHyperparameter("n1", 0, ["a", "b", "c", "d", "e"]),
     NominalHyperparameter("n2", 0, ["x", "y", "z"]), ["a", "c", "e"], ["z", "y", "x"]),
]
TWO_PARAMETERS_NAMES = [case[0].__name__ for case in TWO_PARAMETERS]


@pytest.mark.parametrize("transformer_class, first, second, first_values, second_values", TWO_PARAMETERS,
                         ids=TWO_PARAMETERS_NAMES)
class TestSeveralParameters:
    """
    A transformer can be responsible for several parameters, which it must handle side by side in one frame.
    """

    @staticmethod
    def _setup(transformer_class, first, second, first_values, second_values):
        transformer = transformer_class({"Transformer": {"Type": "test"}}, (first, second))
        return transformer, pd.DataFrame({first.name: first_values, second.name: second_values})

    def test_transforming_several_parameters_at_once_equals_transforming_each_alone(
            self, transformer_class, first, second, first_values, second_values):
        transformer, features = self._setup(transformer_class, first, second, first_values, second_values)

        together = transformer.transform(features)
        alone = transformer.transform(features[[first.name]]).join(transformer.transform(features[[second.name]]))

        # isna() marks the missing cells, the first any() reduces each column, the second any() the whole frame
        assert not together.isna().any().any()
        pd.testing.assert_frame_equal(together, alone)

    def test_decoding_several_parameters_at_once_equals_decoding_each_alone(
            self, transformer_class, first, second, first_values, second_values):
        transformer, features = self._setup(transformer_class, first, second, first_values, second_values)
        first_encoded = transformer.transform(features[[first.name]])
        second_encoded = transformer.transform(features[[second.name]])

        together = transformer.inverse_transform(first_encoded.join(second_encoded))
        alone = transformer.inverse_transform(first_encoded).join(transformer.inverse_transform(second_encoded))

        # isna() marks the missing cells, the first any() reduces each column, the second any() the whole frame
        assert not together.isna().any().any()
        pd.testing.assert_frame_equal(together, alone)
