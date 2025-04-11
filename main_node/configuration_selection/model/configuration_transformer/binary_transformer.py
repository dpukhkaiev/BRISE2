import pandas as pd
from sklearn.pipeline import Pipeline
from typing import Tuple

from configuration_selection.model.configuration_transformer.nominal_transformer_abs import NominalTransformer
from configuration_selection.model.configuration_transformer.sklearn_binary_encoder import BinaryEncoder
from configuration_selection.model.configuration_transformer.sklearn_column_encoder import SklearnColumnTransformer


class BinaryTransformer(NominalTransformer):
    def __init__(self, configuration_transformer_description: dict, relevant_parameters: Tuple):
        super().__init__(configuration_transformer_description, relevant_parameters)
        self.mapping_old_feature_pipeline = {}

    def transform(self, features: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms raw values of parameters (features) according to the selected transformer.
        :param features: raw values of parameters
        :return: transformed features, labels
        """
        # preserve original indexing
        features_ordering = features.columns.tolist()

        # filter relevant features
        relevant_features = self._filter_relevant_features(features)
        if len(relevant_features) == 0:
            return pd.DataFrame()

        intact_features = features.drop(columns=relevant_features.columns)
        if not intact_features.empty:
            self.mapping_old_new_features = dict(
                map(lambda i, j: (i, j), intact_features.columns.tolist(), intact_features.columns.tolist()))
        intact_features['temp_index'] = range(1, len(intact_features) + 1)

        transformed_features = pd.DataFrame()

        for feature_name in relevant_features.columns:
            categories = [list(filter(lambda p: p.name == feature_name, self.relevant_parameters))[0].categories]

            # create encoder object
            encoder = BinaryEncoder(categories)
            encoder = SklearnColumnTransformer(encoder, input_column_names=[feature_name])
            name = list(self.configuration_transformer_description.keys())[0]
            encoder_name = f"{name} for {feature_name}"

            # append to steps
            steps = []
            steps.append((encoder_name, encoder))

            # create pipeline
            features_pipeline = Pipeline(steps)

            # fit transform by pipeline
            transformed_feature = features_pipeline.fit_transform(pd.DataFrame(relevant_features.loc[:, feature_name]))
            self.mapping_old_feature_pipeline[feature_name] = features_pipeline
            if transformed_features.empty:
                transformed_features = pd.DataFrame(transformed_feature)
            else:
                transformed_features = pd.concat([transformed_features, transformed_feature])
            self.mapping_old_new_features[feature_name] = transformed_feature.columns.tolist()

        transformed_features['temp_index'] = range(1, len(transformed_features) + 1)

        merged_features = transformed_features.merge(intact_features, on='temp_index')
        merged_features = merged_features.drop(columns="temp_index")

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
        return super()._inverse_sklearn_transform(transformed_features, self.mapping_old_feature_pipeline)
