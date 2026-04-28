import pandas as pd
import numpy as np
from typing import Union, List

from sklearn.preprocessing import OrdinalEncoder
from sklearn.base import BaseEstimator, TransformerMixin


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
        self.__transformer = OrdinalEncoder(categories=self.__categories, dtype=np.int64)
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

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        if len(df.keys()) != len(self.__n_bits):
            raise TypeError(f"Transformer was fit to data with {self.__n_bits} columns, "
                            f"but given data with {len(df.keys())} columns.")
        # Convert to OrdinalEncoding
        pre_transformed = self.__transformer.transform(X=df)  # In OrdinalEncoding
        # Convert to BinaryEncoding
        n_out_columns = sum(self.__n_bits.values())
        n_out_rows = len(pre_transformed)
        transformed = np.empty(shape=(n_out_rows, n_out_columns), dtype=np.int64)
        for row_idx, p_row in enumerate(pre_transformed):
            row = []
            for idx, cat_idx in enumerate(p_row):
                row.extend(self.__encode_mapping[idx][cat_idx])
            transformed[row_idx] = row
        return transformed

    def inverse_transform(self, df: pd.DataFrame) -> np.ndarray:
        # convert back from Binary to OrdinalEncoding
        ordinal_encoded = pd.DataFrame(columns=list(self.__encode_mapping.keys()))
        # decode per original column
        left_pointer = 0
        for column in self.__encode_mapping.keys():
            columns_idxs = slice(left_pointer, left_pointer + self.__n_bits[column])
            left_pointer += self.__n_bits[column]
            bin_columns_raw = df.iloc[:, columns_idxs].to_numpy()
            bin_columns_real = np.apply_along_axis(self._closest_euclidean,
                                                   axis=1,
                                                   arr=bin_columns_raw,
                                                   vectors=self.__decode_mapping[column].keys())

            ord_column = np.apply_along_axis(lambda enc: self.__decode_mapping[column][tuple(enc)],
                                             axis=1,
                                             arr=bin_columns_real)

            ordinal_encoded[column] = ord_column
        # convert back from OrdinalEncoding to original one
        decoded = self.__transformer.inverse_transform(ordinal_encoded)
        return decoded

    @staticmethod
    def _closest_euclidean(vector: np.ndarray, vectors: List[np.ndarray]) -> np.ndarray:
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
