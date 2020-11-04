from typing import List, Union

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import OrdinalEncoder


class BinaryEncoder(BaseEstimator, TransformerMixin):
    """
    First the categories are encoded as ordinal, then the resulting integers are converted into the binary code,
    then the digits from the binary string are split into separate columns.

    Decoding is done with O(n) complexity by selecting the value of parameter, binary representation of which is the
    closest to one of the existing categories in terms of Euclidean distance.

    Choices object should be hashable.
    """

    def __init__(self, categories: Union[str, List[object]] = 'auto'):

        self.__categories = categories
        self.__transformer = OrdinalEncoder(categories=self.__categories, dtype=pd.np.int64)
        self.__encode_mapping = {}
        self.__decode_mapping = {}
        self.__n_bits = {}
        self._enc_suffix = f"_{self.__class__.__name__}"

    def fit(self, df: pd.DataFrame, y=None):

        self.__transformer.fit(X=df, y=y)
        self.__n_bits = {c_name: len(format(len(c_cats), 'b'))
                         for c_name, c_cats in enumerate(self.__transformer.categories_)}
        # __n_bits reflects how many bits it is needed to encode categories of corresponding (by index) column

        # precompute binary encodings
        for idx, column_categories in enumerate(self.__transformer.categories_):
            self.__encode_mapping[idx] = dict()
            self.__decode_mapping[idx] = dict()
            for cat_idx, category in enumerate(column_categories):
                encoding = tuple(float(x) for x in format(cat_idx, f'0{self.__n_bits[idx]}b'))
                self.__encode_mapping[idx][cat_idx] = encoding
                self.__decode_mapping[idx][encoding] = cat_idx

        return self

    def transform(self, df: pd.DataFrame) -> pd.np.ndarray:

        if len(df.keys()) != len(self.__n_bits):
            raise TypeError(f"Transformer was fit to data with {self.__n_bits} columns, "
                            f"but given data with {len(df.keys())} columns.")
        # Convert to OrdinalEncoding
        pre_transformed = self.__transformer.transform(X=df)    # In OrdinalEncoding
        # Convert to BinaryEncoding
        n_out_columns = sum(self.__n_bits.values())
        n_out_rows = len(pre_transformed)
        transformed = pd.np.empty(shape=(n_out_rows, n_out_columns), dtype=pd.np.int64)
        for row_idx, p_row in enumerate(pre_transformed):
            row = []
            for idx, cat_idx in enumerate(p_row):
                row.extend(self.__encode_mapping[idx][cat_idx])
            transformed[row_idx] = row
        return transformed

    def inverse_transform(self, df: pd.DataFrame) -> pd.np.ndarray:

        # convert back from Binary to OrdinalEncoding
        ordinal_encoded = pd.DataFrame(columns=self.__encode_mapping.keys())
        # decode per original column
        left_pointer = 0
        for column in self.__encode_mapping.keys():
            columns_idxs = slice(left_pointer, left_pointer + self.__n_bits[column])
            left_pointer += self.__n_bits[column]
            bin_columns_raw = df.iloc[:, columns_idxs].to_numpy()
            bin_columns_real = pd.np.apply_along_axis(self._closest_euclidean,
                                                      axis=1,
                                                      arr=bin_columns_raw,
                                                      vectors=self.__decode_mapping[column].keys())

            ord_column = pd.np.apply_along_axis(lambda enc: self.__decode_mapping[column][tuple(enc)],
                                                axis=1,
                                                arr=bin_columns_real)

            ordinal_encoded[column] = ord_column
        # convert back from OrdinalEncoding to original one
        decoded = self.__transformer.inverse_transform(ordinal_encoded)
        return decoded

    @staticmethod
    def _closest_euclidean(vector: pd.np.ndarray, vectors: List[pd.np.ndarray]) -> pd.np.ndarray:
        """
        finds closest vector from a list of provided vectors by minimizing Euclidean distance
        :param vector:
        :param vectors:
        :return:
        """
        min_found_distance = float('inf')
        closest_vector = None
        for existing_vector in vectors:
            dist = sum(((x - y) ** 2 for x, y in zip(vector, existing_vector)))
            if dist == 0:
                # Found exact match
                closest_vector = existing_vector
                break
            elif dist < min_found_distance:
                closest_vector = existing_vector
                min_found_distance = dist
        return closest_vector


class SklearnColumnTransformer(BaseEstimator, TransformerMixin):
    """
    Object Decorator for Sklearn-based preprocessing units.
    The main intense of object is to maintain pandas.DataFrame structure of data,
    while applying different preprocessing steps to different columns of input pandas.DataFrame.

    Example:
    --------
        >>>from preprocessing.transformers import SklearnColumnTransformer
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
        # Select needed columns
        df_to_transform = df[self.input_column_names]
        transformed_raw = self.transformer.transform(df_to_transform)

        # Replace data in columns
        if df_to_transform.shape != transformed_raw.shape:
            self.out_column_names = ["_".join(self.input_column_names)
                                     + self._enc_suffix
                                     + str(x) for x in range(transformed_raw.shape[1])]
        else:
            self.out_column_names = [name + self._enc_suffix for name in self.input_column_names]
        transformed_df = pd.DataFrame(transformed_raw, columns=self.out_column_names)
        df = df.drop(columns=self.input_column_names).join(transformed_df)

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
