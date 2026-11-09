import pandas as pd
from sklearn.pipeline import Pipeline
from typing import Tuple

from configuration_selection.model.configuration_transformer.integer_transformer_abs import IntegerTransformer
from configuration_selection.model.configuration_transformer.sklearn_column_encoder import SklearnColumnTransformer
from sklearn.preprocessing import MinMaxScaler


class SklearnIntegerTransformer(IntegerTransformer):
    def __init__(self, configuration_transformer_description: dict, relevant_parameters: Tuple,
                 parameters_with_inactive_value: frozenset = frozenset()):
        super().__init__(configuration_transformer_description, relevant_parameters, parameters_with_inactive_value)
        self.mapping_old_feature_pipeline = {}

    def transform(self, features: pd.DataFrame) -> pd.DataFrame:
        # preserve original indexing
        features_ordering = features.columns.tolist()

        # filter relevant features
        relevant_features = self._filter_relevant_features(features)
        if len(relevant_features) == 0:
            return pd.DataFrame()

        # the rows are joined by position, whatever the index of the features
        intact_features = features.drop(columns=relevant_features.columns).reset_index(drop=True)
        if not intact_features.empty:
            self.mapping_old_new_features = dict(
                map(lambda i, j: (i, j), intact_features.columns.tolist(), intact_features.columns.tolist()))

        transformed_features = pd.DataFrame()

        for feature_name in relevant_features.columns:
            features_pipeline = self._get_or_build_pipeline(feature_name)

            # transform only - the pipeline was already fit once, on the hyperparameter's own bounds
            transformed_feature = features_pipeline.transform(pd.DataFrame(relevant_features.loc[:, feature_name]))
            if transformed_features.empty:
                transformed_features = pd.DataFrame(transformed_feature)
            else:
                transformed_features = pd.concat([transformed_features, transformed_feature], axis=1)
            self.mapping_old_new_features[feature_name] = transformed_feature.columns.tolist()

        merged_features = pd.concat([transformed_features, intact_features], axis=1)

        # sort
        sorted_transformed = []
        for f in features_ordering:
            t_f = self.mapping_old_new_features[f]
            if type(t_f) is str:
                sorted_transformed.append(t_f)
            else:
                sorted_transformed = sorted_transformed + t_f

        result = merged_features.reindex(columns=sorted_transformed)

        return result

    def inverse_transform(self, transformed_features: pd.DataFrame) -> pd.DataFrame:
        # If optimizers propose continuous values, scaling them back and casting to int would
        # truncate, so that the upper bound is reachable only at exactly 1. Decode through the hyperparameter's
        # equal-width bins instead (Hyperparameter.transform), the same rule sampling uses.
        decoded = []
        for feature_name in self.mapping_old_feature_pipeline:
            column = self.mapping_old_new_features[feature_name][0]
            if column not in transformed_features.columns:
                continue
            hyperparameter = list(filter(lambda p: p.name == feature_name, self.relevant_parameters))[0]
            values = [hyperparameter.transform(min(max(value, 0), 1)) for value in transformed_features[column]]
            decoded.append(pd.DataFrame({feature_name: values}, index=transformed_features.index))
        return pd.concat(decoded, axis=1) if decoded else pd.DataFrame()

    def _get_or_build_pipeline(self, feature_name: str) -> Pipeline:
        """
        Build and fit this feature's Pipeline once, from the hyperparameter's own [lower, upper] bounds -
        not from whatever batch of rows happens to be passed to transform(). A MinMaxScaler fit on the rows
        passed at prediction time (often just one row) would scale every value to 0, since a single point
        always sits at its own min and max; fitting on the actual bounds instead keeps scaling consistent
        between training and prediction, and every later transform() call reuses this fitted pipeline.
        """
        if feature_name in self.mapping_old_feature_pipeline:
            return self.mapping_old_feature_pipeline[feature_name]

        hyperparameter = list(filter(lambda p: p.name == feature_name, self.relevant_parameters))[0]
        reference_data = pd.DataFrame({feature_name: [hyperparameter.get_lower(), hyperparameter.get_upper()]})

        encoder = MinMaxScaler()
        encoder = SklearnColumnTransformer(encoder, input_column_names=[feature_name])
        name = list(self.configuration_transformer_description.keys())[0]
        encoder_name = f"{name} for {feature_name}"

        features_pipeline = Pipeline([(encoder_name, encoder)])
        features_pipeline.fit(reference_data)

        self.mapping_old_feature_pipeline[feature_name] = features_pipeline
        return features_pipeline
