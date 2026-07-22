import importlib
import pandas as pd
from typing import Dict, Tuple


from configuration_selection.model.surrogate.surrogate_abs import Surrogate


class SklearnWrapper(Surrogate):
    def __init__(self, surrogate_description: Dict, region: Tuple, objectives: Dict):
        super().__init__(surrogate_description, region, objectives)

        self.multi_objective = surrogate_description['Instance'][self.feature_name]['MultiObjective']

        full_path = surrogate_description['Instance'][self.feature_name]['Class']
        module_name, class_name = full_path.rsplit('.', 1)

        module = importlib.import_module(module_name)
        surrogate_class = getattr(module, class_name)

        if 'Parameters' in surrogate_description['Instance'][self.feature_name].keys():
            self.surrogate_instance = surrogate_class(**surrogate_description['Instance'][self.feature_name]['Parameters'])
        else:
            self.surrogate_instance = surrogate_class()

    def create(self, features: pd.DataFrame, labels: pd.DataFrame) -> bool:

        transformed_features = self._transform_configuration(features)
        transformed_labels = self._transform_values(labels)

        # A single-objective label is a (n, 1) column-vector; single-target sklearn
        # estimators expect a 1d (n,) array and otherwise warn (DataConversionWarning).
        # A genuine multi-output label (>1 column) is left as is.
        if transformed_labels.shape[1] == 1:
            transformed_labels = transformed_labels.to_numpy().ravel()

        self.surrogate_instance.fit(transformed_features, transformed_labels)
        return True

    def predict(self, cfg: pd.Series, transform: bool = True) -> pd.DataFrame:
        # Series to Dataframe
        configuration = pd.DataFrame(columns=cfg.index)
        configuration.loc[0] = cfg.values

        if transform:
            transformed_configuration = self._transform_configuration(configuration)
        else:
            transformed_configuration = configuration

        predicted = self.surrogate_instance.predict(transformed_configuration)
        if not self.scalarized:
            result = pd.DataFrame(predicted, columns=list(self.objectives.keys()))
        else:
            result = pd.DataFrame(predicted, columns=["Y"])

        return result

    def _transform_values(self, labels: pd.DataFrame) -> pd.DataFrame:
        # flatten labels to be 1d-array
        transformed_labels = super()._transform_values(labels)
        
        if isinstance(transformed_labels, pd.DataFrame) and transformed_labels.shape[1] == 1:
            return transformed_labels.iloc[:, 0].values.ravel()
            
        return transformed_labels