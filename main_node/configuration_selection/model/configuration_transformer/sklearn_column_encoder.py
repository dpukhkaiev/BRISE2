import pandas as pd

from typing import List
from sklearn.base import BaseEstimator, TransformerMixin


class SklearnColumnTransformer(BaseEstimator, TransformerMixin):
    """
    Object Decorator for Sklearn-based preprocessing units.
    The main intense of object is to maintain pandas.DataFrame structure of data,
    while applying different preprocessing steps to different columns of input pandas.DataFrame.

    Example:
    --------
        >>>from configuration_selection.model.configuration_transformer.sklearn_column_encoder import SklearnColumnTransformer
        >>>from sklearn.preprocessing import OrdinalEncoder as SKEnc
        >>>import pandas as pd

        >>>data = pd.DataFrame({'numeric_data': [1, 2, 3, 1, 2], 'categorical_data':[10, 20, 50, 10, 20]})

        # initialize sklearn encoder and wrap it by SklearnColumnTransformer specifying columns for preprocessing
        >>>unique_categories = list(set(data['categorical_data']))
        >>>base_enc = SklearnColumnTransformer(SKEnc(categories=[unique_categories]), column_names=['categorical_data'])

        # transform
        >>>transformed = base_enc.fit_transform(data)
        >>>print(transformed)
           numeric_data  categorical_data_OrdinalEncoder
        0             1                              0.0
        1             2                              1.0
        2             3                              2.0
        3             1                              0.0
        4             2                              1.0

        # inverse transformation
        >>>inversed = base_enc.inverse_transform(transformed)
        >>>print(inversed)
           numeric_data  categorical_data
        0             1                10
        1             2                20
        2             3                50
        3             1                10
        4             2                20
    """

    def __init__(self, transformer: (BaseEstimator, TransformerMixin), input_column_names: List[str] = None):
        """
        SklearnColumnTransformer is an adapter for sklearn.preprocessing transformers,
        that enables Sklearn transformers to be applied to specific column in pandas DataFrame.

        :param transformer: initialized Sklearn transformer.
        :param input_column_names: names of columns to apply transformer.
        """

        self.transformer = transformer
        self.input_column_names = input_column_names
        self.out_column_names = None
        self.original_data_types = {}
        self._enc_suffix = f"_{self.transformer.__class__.__name__}"

    def fit(self, df: pd.DataFrame, y=None, **fit_params):
        if not self.input_column_names:
            # If column_names parameter was provided in 'fit' - use it, otherwise - apply transformation to all columns.
            self.input_column_names = fit_params.get("column_names", None) or df.keys().tolist()
        self.original_data_types = df.dtypes.to_dict()
        self.transformer = self.transformer.fit(df[self.input_column_names], y=y, **fit_params)
        return self

    def transform(self, df: pd.DataFrame, y=None) -> pd.DataFrame:
        df = df.copy(deep=True)
        df['temp_index'] = range(1, len(df) + 1)
        # Select needed columns
        df_to_transform = df[self.input_column_names]
        transformed_raw = self.transformer.transform(df_to_transform)

        # Replace data in columns
        if df_to_transform.shape != transformed_raw.shape:
            self.out_column_names = ["_".join(self.input_column_names) + self._enc_suffix + str(x) for x in
                                     range(transformed_raw.shape[1])]
        else:
            self.out_column_names = [name + self._enc_suffix for name in self.input_column_names]
        transformed_df = pd.DataFrame(transformed_raw, columns=self.out_column_names)
        transformed_df['temp_index'] = range(1, len(transformed_df) + 1)
        df = df.merge(transformed_df, on="temp_index")
        df = df.drop(columns=self.input_column_names)
        df = df.drop(columns='temp_index')

        return df

    def inverse_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy(deep=True)
        # Select and transform back needed columns
        to_transform = df[self.out_column_names]
        transformed_raw = self.transformer.inverse_transform(to_transform)

        # Replace data in columns
        for idx, c_name in enumerate(self.input_column_names):
            df[c_name] = transformed_raw.T[idx]
        df = df.drop(columns=self.out_column_names)
        df = df.astype(self.original_data_types)

        return df
