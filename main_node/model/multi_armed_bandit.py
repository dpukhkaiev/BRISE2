import logging

from typing import Mapping

import numpy as np
import pandas as pd
from core_entities.search_space import CategoricalHyperparameter
from model.model_abs import Model


class MultiArmedBandit(Model):
    """
    inspired by "A Multi-Armed Bandit selection strategy for Hyper-heuristics"
    Ferreira, Alexandre Silvestre Goncalves, Richard Aderbal Pozo, Aurora

    enhancements:
    - adaptive window
    - adaptive C coefficient to balance exploration - exploitation
    :return:
    """

    def __init__(self, parameters: Mapping):
        super().__init__(parameters=parameters)
        if not isinstance(parameters['c'], (int, float)) and parameters['c'] != 'std':
            raise TypeError("Parameter 'c' should be number or 'std'.")

        self.categories_info = {}

    def build_model(
            self, features: pd.DataFrame, labels: pd.DataFrame, features_description: Mapping, is_minimization: bool
    ) -> bool:
        if is_minimization:
            raise TypeError("Multi Armed Bandit optimizer performs only maximization tasks!")
        self.is_built = False
        objective_column: str = labels.keys()[0]  # by definition, this model works with solution improvement.

        # --- Validate input
        for h_name in features_description:
            if not isinstance(features_description[h_name]["hyperparameter"], CategoricalHyperparameter):
                msg = f"Multi Armed Bandit optimization supports only Categorical hyperparameters. " \
                      f"The type of hyperparameter {h_name} is {type(features_description[h_name]['hyperparameter'])}"
                logging.getLogger(__name__).error(msg)
                return self.is_built

        self.features_description = features_description

        # for each category in each hyperparameter calculate:
        # 1. number of times it was used
        # 2. quality (avg improvement)
        categories_info = {}
        for feature_name in self.features_description:
            categories_info[feature_name] = {}
            for feature_category in self.features_description[feature_name]['categories']:
                category_features = features[features[feature_name] == feature_category]
                category_used_times = len(category_features)

                # MAB could properly evaluate only those categories, which were probed at least once thus,
                # we encourage to evaluate not evaluated yet categories
                if category_used_times > 0:
                    category_quality = sum(labels.iloc[category_features.index][objective_column]) \
                        / category_used_times
                else:
                    category_quality = np.inf

                categories_info[feature_name][feature_category] = {
                    "times used": category_used_times,
                    "quality": category_quality,
                    "UCB_value": 0  # will be calculated later, since it depends on quality of other categories
                }
        # 3. calculate UCB value of each category in every hyperparameter
        for feature_name in self.features_description:
            for feature_category in self.features_description[feature_name]['categories']:
                exploration_rate = np.sqrt(
                    np.divide(
                        2 * np.log(len(labels)),
                        categories_info[feature_name][feature_category]["times used"]
                    )
                )
                if np.isnan(exploration_rate):
                    # only one, but not this category was used (in previous formula nominator=inf and denominator=inf).
                    exploration_rate = np.inf
                exploitation_rate = categories_info[feature_name][feature_category]["quality"]
                if isinstance(self.parameters['c'], (int, float)):
                    c = self.parameters['c']
                else:
                    if len(labels[objective_column]) > 1:
                        c = np.std(labels[objective_column])   # * 10
                    else:
                        c = 1   # to avoid 'nan's in following formula
                categories_info[feature_name][feature_category]["UCB_value"] = exploitation_rate + c * exploration_rate
        self.categories_info = categories_info
        self.is_built = True
        return self.is_built

    def predict(self) -> pd.DataFrame:
        prediction = {}
        # predict category for each categorical hyperparameter
        # selecting among categories with the highest UCB value
        for feature_name in self.features_description:
            max_ucb = float("-inf")
            for category in self.categories_info[feature_name]:
                ucb_value = self.categories_info[feature_name][category]["UCB_value"]
                if ucb_value > max_ucb:
                    max_ucb = ucb_value
            candidate_categories = list(
                filter(
                    lambda cat: self.categories_info[feature_name][cat]["UCB_value"] == max_ucb,
                    self.categories_info[feature_name]
                )
            )
            prediction[feature_name] = candidate_categories[np.random.randint(len(candidate_categories))]
        prediction_as_df = pd.DataFrame(data=[prediction])
        return prediction_as_df
