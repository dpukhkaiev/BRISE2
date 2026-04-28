import numpy as np
import logging

import pandas as pd
from typing import Dict, Tuple

from configuration_selection.model.surrogate.surrogate_abs import Surrogate
from core_entities.search_space import CategoricalHyperparameter


class MultiArmedBandit(Surrogate):

    def __init__(self, surrogate_description: Dict, region: Tuple, objectives: Dict):
        super().__init__(surrogate_description, region, objectives)
        self.objective = self.objectives[list(self.objectives.keys())[0]]  # FRAMAB is always single-objective
        self.multi_objective = surrogate_description['Instance']['MultiArmedBandit']['MultiObjective']
        self.c = surrogate_description['Instance']['MultiArmedBandit']['Parameters']['c']

    def create(self, features: pd.DataFrame, labels: pd.DataFrame) -> bool:
        if self.objective["Minimization"]:
            raise TypeError("Multi Armed Bandit optimizer performs only maximization tasks!")

        transformed_features = self._transform_configuration(features)
        transformed_labels = self._transform_values(labels)

        objective_column: str = transformed_labels.keys()[0]  # by definition, this model works with solution improvement.

        # --- Validate input
        for hp in self.region:
            if not isinstance(hp, CategoricalHyperparameter):
                msg = f"Multi Armed Bandit optimization supports only Categorical hyperparameters. " \
                      f"The type of hyperparameter {hp.name} is {hp.type}"
                logging.getLogger(__name__).error(msg)
                return False

        # for each category in each hyperparameter calculate:
        # 1. number of times it was used
        # 2. quality (avg improvement)
        categories_info = {}
        for hp in self.region:
            categories_info[hp.name] = {}
            for feature_category in hp.categories:
                category_features = transformed_features[transformed_features[hp.name] == feature_category]
                category_used_times = len(category_features)

                # MAB could properly evaluate only those categories, which were probed at least once thus,
                # we encourage to evaluate not evaluated yet categories
                if category_used_times > 0:
                    category_quality = sum(
                        transformed_labels.iloc[category_features.index][objective_column]) / category_used_times
                else:
                    category_quality = np.inf

                categories_info[hp.name][feature_category] = {
                    "times used": category_used_times,
                    "quality": category_quality,
                    "UCB_value": 0  # will be calculated later, since it depends on quality of other categories
                }
        # 3. calculate UCB value of each category in every hyperparameter
        for hp in self.region:
            for feature_category in hp.categories:
                exploration_rate = np.sqrt(
                    np.divide(
                        2 * np.log(len(transformed_labels)),
                        categories_info[hp.name][feature_category]["times used"]
                    )
                )
                if np.isnan(exploration_rate):
                    # only one, but not this category was used (in previous formula nominator=inf and denominator=inf).
                    exploration_rate = np.inf
                exploitation_rate = categories_info[hp.name][feature_category]["quality"]
                if isinstance(self.c, (int, float)):
                    c = self.c
                else:
                    if len(transformed_labels[objective_column]) > 1:
                        c = np.std(transformed_labels[objective_column])  # * 10
                    else:
                        c = 1  # to avoid 'nan's in following formula
                categories_info[hp.name][feature_category]["UCB_value"] = exploitation_rate + c * exploration_rate
        self.categories_info = categories_info
        return True

    def predict(self, cfg: pd.Series, transform: bool = True) -> pd.DataFrame:
        # Multi-armed bandit does not predict an objective function, but calculates an upper confidence bound,
        # "optimism in the face of uncertainty", higher is better
        # WARNING: general validators cannot be used
        ucbs = []
        for hp_name in cfg.index:
            ucb = self.categories_info[hp_name][cfg[hp_name]]["UCB_value"]
            ucbs.append(ucb)
        summed_ucb = sum(ucbs)
        if not self.scalarized:
            result = pd.DataFrame([summed_ucb], columns=list(self.objectives.keys()))
        else:
            result = pd.DataFrame([summed_ucb], columns=["Y"])

        return result
