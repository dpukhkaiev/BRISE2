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
from configuration_selection.model.configuration_transformer.sklearn_column_encoder import SklearnColumnTransformer
from configuration_selection.model.configuration_transformer.sklearn_binary_transformer import SklearnBinaryTransformer
from configuration_selection.model.configuration_transformer.sklearn_float_transformer import SklearnFloatTransformer
from configuration_selection.model.configuration_transformer.sklearn_integer_transformer import SklearnIntegerTransformer
from configuration_selection.model.configuration_transformer.sklearn_ordinal_transformer import SklearnOrdinalTransformer

FLOAT = FloatHyperparameter("f", 0, 2.0, 6.0)
INTEGER = IntegerHyperparameter("i", 0, 1, 10)
ORDINAL = OrdinalHyperparameter("o", 0, ["a", "b", "c", "d"])
NOMINAL = NominalHyperparameter("n", 0, ["a", "b", "c", "d"])


def _transformer(transformer_class, hyperparameter):
    return transformer_class({"Transformer": {"Type": "test"}}, (hyperparameter,))


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

    def test_transforming_a_batch_gives_the_same_encoding_as_transforming_each_row_alone(self):
        values = [2.0, 3.1, 4.7, 6.0]
        transformer = _transformer(SklearnFloatTransformer, FLOAT)

        batch = transformer.transform(pd.DataFrame({"f": values})).iloc[:, 0].tolist()
        rows = [transformer.transform(pd.DataFrame({"f": [v]})).iloc[0, 0] for v in values]

        assert batch == rows

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

    def test_every_pipeline_a_transformer_builds_is_fitted(self):
        cases = ((SklearnFloatTransformer, FLOAT, 3.0), (SklearnIntegerTransformer, INTEGER, 5),
                 (SklearnOrdinalTransformer, ORDINAL, "b"), (SklearnBinaryTransformer, NOMINAL, "b"))
        for transformer_class, hyperparameter, value in cases:
            transformer = _transformer(transformer_class, hyperparameter)

            transformer.transform(pd.DataFrame({hyperparameter.name: [value]}))

            assert len(transformer.mapping_old_feature_pipeline) == 1
            for pipeline in transformer.mapping_old_feature_pipeline.values():
                check_is_fitted(pipeline)
