import pandas as pd
import numpy as np
from typing import Tuple, List, Dict
from sklearn.model_selection import KFold, ShuffleSplit
from sklearn.metrics import r2_score
from math import isnan

from configuration_selection.model.validator.validator_abs import Validator
from configuration_selection.model.surrogate.surrogate_abs import Surrogate
from configuration_selection.model.value_transformer.value_scalarizator_abs import ValueScalarizator


class QualityValidator(Validator):

    def __init__(self, validator_description: Dict, region: Tuple, objectives: Dict):
        super().__init__(validator_description, region, objectives)
        self.validator_description = validator_description
        self.quality_threshold = self.validator_description["QualityThreshold"]
        self.split = list(self.validator_description["Split"].keys())[0]
        self.splitter = None
        if self.split == "HoldOut":
            self.training_set_size = self.validator_description["Split"][self.split]["TrainingSet"]
            self.splitter = ShuffleSplit(n_splits=1, test_size=1-self.training_set_size)
        elif self.split == "KFold":
            self.splitter = KFold(self.validator_description["Split"][self.split]["NumberOfFolds"])

    def validate(self, surrogate: Surrogate, features: pd.DataFrame, labels: pd.DataFrame) -> Tuple[bool, float]:
        if len(features) <= 2:  # not enough configurations for validation
            return False, float(-np.inf)
        predicted = pd.DataFrame()
        for i, f in features.iterrows():
            p = surrogate.predict(f)
            if predicted.empty:
                predicted = p
            else:
                predicted = pd.concat([predicted, p])
        if not surrogate.scalarized:
            # TODO multi-objective validation. currently weighted as uniform average
            score = r2_score(labels.values, predicted.values)
        else:
            vt: ValueScalarizator = list(filter(lambda vt: issubclass(type(vt), ValueScalarizator), surrogate.value_transformers))[0]
            score = r2_score(vt.transform(labels), predicted.values)

        if isnan(score):
            return False, float(-np.inf)
        elif score > self.quality_threshold:
            return True, score
        else:
            return False, float(-np.inf)

    def train_test_split(self, features: pd.DataFrame, labels: pd.DataFrame) -> Tuple[List[pd.DataFrame], List[pd.DataFrame], List[pd.DataFrame], List[pd.DataFrame]]:
        train_features: List[pd.DataFrame] = []
        train_labels: List[pd.DataFrame] = []
        test_features: List[pd.DataFrame] = []
        test_labels: List[pd.DataFrame] = []
        try:
            for _, (train_indices, test_indices) in enumerate(self.splitter.split(features.to_numpy(), labels.to_numpy())):
                train_features.append(features.iloc[train_indices])
                train_labels.append(labels.iloc[train_indices])
                test_features.append(features.iloc[test_indices])
                test_labels.append(labels.iloc[test_indices])

            return train_features, train_labels, test_features, test_labels

        except ValueError:
            train_features.append(pd.DataFrame())
            train_labels.append(pd.DataFrame())
            test_features.append(pd.DataFrame())
            test_labels.append(pd.DataFrame())
            return train_features, train_labels, test_features, test_labels
