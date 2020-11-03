import copy
import logging
from collections import OrderedDict
from typing import List, Mapping

import pandas as pd
from core_entities.configuration import Configuration
from core_entities.search_space import Hyperparameter
from model.model_selection import get_model


class Predictor:
    """
    This class abstract notion of prediction within tree-shaped search space from the underlying models.
    The underlying models see only the current level with related data that is going to be operated in it,
    no other level data exposed for it.

    Responsibilities:
        - hide structure of tree-shaped search space.
        - provide data and data description for underlying models about current level.
        - select underlying model for each level
    """

    def __init__(self, experiment_id: str, experiment_description: Mapping, search_space: Hyperparameter):
        self.experiment_id = experiment_id
        self.predictor_config = experiment_description["Predictor"]
        self.task_config = experiment_description["TaskConfiguration"]
        self.search_space = search_space
        self.logger = logging.getLogger(__name__)

    def predict(self, measured_configurations: List[Configuration]) -> Configuration:
        """
        Predict next Configuration using already evaluated configurations.
        Prediction is a construction process and it is done in iterations.
        It stops after constructing the valid Configuration within the Search Space.
        Each iteration uncovers and predicts new Hyperparameters deeper in the Search Space.

        :param measured_configurations: a list of already measured Configurations that will be used to make a
        prediction.
        :return: Configuration that is going to be measured.

        Question: need to transfer data from the previous level? (that was fixed and will not be changed)
          - more no than yes.
              for no:
                - less data to (pre)process - less dimensions
                - less ad-hoc solutions on "how to differentiate in data???" - simply predict over all dimensions,
                other are targets.
              for yes:
                - models will be more accurate (?)
         """
        level = -1
        parameters = OrderedDict()
        # Select the latest Configurations, according to the window size
        if isinstance(self.predictor_config["window size"], int):
            number_of_configs_to_consider = self.predictor_config["window size"]
        else:
            # meaning self.window_size, float)
            number_of_configs_to_consider = \
                int(round(self.predictor_config["window size"] * len(measured_configurations)))
        level_configs = measured_configurations[len(measured_configurations) - number_of_configs_to_consider:]

        # Check if entire configuration is valid now.
        while not self.search_space.validate(parameters, is_recursive=True):
            level += 1  # it is here because of 'continue'

            # 1. Filter Configurations.
            level_configs = list(filter(
                lambda x: self.search_space.are_siblings(parameters, x.parameters),  # Filter
                level_configs   # Input data for filter
            ))

            if not level_configs:
                # If there is no data on current level, just use random sampling
                self.search_space.generate(parameters)
                continue

            # 2. Derive which parameters will be predicted on this level:
            # - by expanding the parameters from previous level to this level
            # - by removing information from the previous level(s)
            dummy = copy.deepcopy(parameters)
            self.search_space.generate(dummy)
            description = self.search_space.describe(dummy)
            for hyperparameter in parameters:
                del description[hyperparameter]

            # 4. Select and build model, predict parameters for this level
            # 4.1. Select and create model from ED
            # 4.2. Transform Configurations into Pandas DataFrame keeping only relevant for this level information,
            # split features and labels
            # 4.3. Build model
            # 4.4. Make a prediction as PD DataFrame or None
            # 4.5. Validate a prediction: results could be out of bound or more sophisticated cases (in future)

            # 4.1.
            model_parameters = \
                self.predictor_config["models"][level if len(self.predictor_config["models"]) > level else -1]
            model = get_model(model_parameters)

            # 4.2.
            feature_columns = list(description.keys())
            highest_priority_objective_index = self.task_config["ObjectivesPrioritiesModels"]\
                .index(max(self.task_config["ObjectivesPrioritiesModels"]))

            highest_priority_objective = self.task_config["Objectives"][highest_priority_objective_index]

            data = pd.DataFrame(
                [cfg.to_series()[feature_columns + [highest_priority_objective]] for cfg in level_configs])

            features = pd.DataFrame(data[feature_columns])
            labels = pd.DataFrame(data[highest_priority_objective])

            # 4.3
            is_minimization = self.task_config["ObjectivesMinimization"][highest_priority_objective_index]
            model.build_model(features, labels, description, is_minimization)
            # 4.4
            if model.is_built:
                pd_prediction = model.predict()
                prediction = pd_prediction.to_dict(orient="records")
                if len(prediction) > 1:
                    self.logger.warning(f"Model predicted more than 1 parameters set. "
                                        f"Only first valid will be used{prediction[0]}.")
                # 4.5
                valid_prediction_found = False
                for predicted_hyperparameters in prediction:
                    valid_prediction_found = True
                    for hyperparameter_name in description.keys():
                        hyperparameter = description[hyperparameter_name]["hyperparameter"]
                        # Validation should be encapsulated if more sophisticated approaches arise.
                        if not hyperparameter.validate(predicted_hyperparameters, is_recursive=False):
                            valid_prediction_found = False
                            break
                    if valid_prediction_found:
                        break
                    else:
                        continue

                if not valid_prediction_found:
                    self.logger.warning("Model did not predict valid hyperparameter set. Sampling random.")
                    self.search_space.generate(parameters)
                else:
                    if any((h_name in parameters for h_name in predicted_hyperparameters)):
                        raise ValueError(f"Previously selected hyperparameters should not be altered! "
                                         f"Previous: {parameters}. This level: {predicted_hyperparameters}")
                    parameters.update(predicted_hyperparameters)
            else:
                self.logger.debug(
                    f"{model_parameters['Type']} model was not build to predict hyperparameters: {list(description.keys())}. "
                    f"Random values will be sampled.")
                self.search_space.generate(parameters)

        return Configuration(parameters, Configuration.Type.PREDICTED, self.experiment_id)
