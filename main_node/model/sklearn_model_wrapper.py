from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd
from model.model_abs import Model
from preprocessing.pipelines import build_preprocessing_pipelines
from selection.description_selection import description_selection
from sklearn.linear_model.base import LinearModel
from sklearn.model_selection import LeaveOneOut, ShuffleSplit, cross_val_score
from sklearn.pipeline import Pipeline


class SklearnModelWrapper(Model):

    def __init__(self, model: LinearModel, parameters: Mapping):
        super().__init__(parameters)
        self.model = model
        self.model_score: float = 0.0

        self.label_keys: pd.core.indexes.base.Index = None
        self.t_label_keys: pd.core.indexes.base.Index = None
        self.feature_keys: pd.core.indexes.base.Index = None

        self.features_prp: Pipeline = None
        self.label_prp: Pipeline = None
        self.is_minimization = None

    def build_model(
            self, features: pd.DataFrame, labels: pd.DataFrame, features_description: Mapping, is_minimization: bool
    ) -> bool:
        self.is_minimization = is_minimization
        self.label_keys = labels.keys()
        self.feature_keys = features.keys()
        self.features_description = features_description

        # 1. Preprocess data
        features_prp, labels_prp = build_preprocessing_pipelines(self.parameters["DataPreprocessing"], features_description)
        self.features_prp = features_prp
        self.label_prp = labels_prp

        t_features = self.features_prp.fit_transform(features)
        t_labels = self.label_prp.fit_transform(labels)
        self.t_label_keys = t_labels.keys()

        # 2. Test model accuracy on data
        if len(t_features) < 2:
            self.model_score = 0
            self.is_built = False
        else:
            if 2 <= len(t_features) < self.parameters["CrossValidationSplits"]:
                validator = LeaveOneOut()
            else:
                validator = ShuffleSplit(n_splits=self.parameters["CrossValidationSplits"],
                                         test_size=self.parameters["TestSize"])

            score = cross_val_score(self.model, X=t_features, y=t_labels, cv=validator)

            # 3. Check if model accuracy is affordable
            self.model_score = np.average(score)
            if self.model_score < self.parameters["MinimalScore"]:
                self.is_built = False
            else:
                # 4. Keep built model if it is good enough
                self.model.fit(t_features, t_labels)
                self.is_built = True
        return self.is_built

    def predict(self) -> pd.DataFrame:

        if not self.is_built:
            raise RuntimeError("Model should be built before making a prediction.")

        sampled_hyperparameters = []
        for _ in range(self.parameters["SamplingSize"]):
            sampled_hyperparameters.append(description_selection(self.features_description))
        sampled_f: pd.DataFrame = pd.DataFrame(data=sampled_hyperparameters)

        t_sampled_f: pd.DataFrame = self.features_prp.transform(sampled_f)
        t_predicted_l = pd.DataFrame(data=self.model.predict(t_sampled_f), columns=self.t_label_keys)
        predicted_l: pd.DataFrame = self.label_prp.inverse_transform(t_predicted_l)

        idx_from_best_to_worse = predicted_l.sort_values(
            by=self.label_keys.to_list(), ascending=[self.is_minimization]
        ).index

        # pick the best transformed feature set and inverse it transformation - it is out prediction
        prediction: pd.DataFrame = self.features_prp.inverse_transform(t_sampled_f.iloc[[idx_from_best_to_worse[0]]])

        if not set(self.feature_keys) == set(prediction.keys()):
            raise ValueError(f"Prediction hyperparameter names do not match used to fit the model: "
                             f"{set(self.feature_keys)} != {set(prediction.keys())}. Plase, check preprocessing, model")
        return prediction
