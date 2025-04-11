# BSD 3-Clause License

# Copyright (c) 2017-2018, ML4AAD
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import pandas as pd
import numpy as np
import statsmodels.api as sm
from typing import Dict, Tuple

from core_entities.search_space import (
    Hyperparameter,
    NominalHyperparameter,
    NumericHyperparameter,
    OrdinalHyperparameter
)
from configuration_selection.model.surrogate.surrogate_abs import Surrogate


class TreeParzenEstimator(Surrogate):
    def __init__(self, surrogate_description: Dict, region: Tuple, objectives: Dict):
        super().__init__(surrogate_description, region, objectives)
        self.objective = self.objectives[list(self.objectives.keys())[0]]  # TPE is always single-objective
        self.min_bandwidth = surrogate_description["Instance"][self.feature_name]["Parameters"]["min_bandwidth"]
        self.random_fraction = surrogate_description["Instance"][self.feature_name]["Parameters"]["random_fraction"]
        self.top_n_percent = surrogate_description["Instance"][self.feature_name]["Parameters"]["top_n_percent"]
        self.kde_vartypes = ""
        self.varsizes = []
        self.model = {}

    def create(self, features: pd.DataFrame, labels: pd.DataFrame) -> bool:
        is_built = False

        # Skip with predefined probability
        if np.random.rand() <= self.random_fraction:
            return is_built

        # 1. Check if enough data in model.
        min_points_in_model = len(features.keys()) + 1
        n_good = max(min_points_in_model, (self.top_n_percent * features.shape[0]) // 100)

        if len(features) < n_good * 2:
            return is_built

        transformed_features = self._transform_configuration(features)
        transformed_labels = self._transform_values(labels)
        transformed_labels.reset_index(inplace=True, drop=True)  # reindex, since transformation changes indices

        sorted_labels = labels.sort_values(by=transformed_labels.keys()[0], ascending=self.objective["Minimization"])

        t_features_good = transformed_features.iloc[sorted_labels[:n_good].index]
        t_features_bad = transformed_features.iloc[sorted_labels[n_good:].index]

        # WARNING: If you change transformer types you need to take care of `vartypes` specified for statsmodels KDE!
        self.kde_vartypes = ""
        self.varsizes = []

        # determine types of hyperparameters from columns and, if categorical - the number of choices it has
        for column_name in transformed_features.keys():
            hyperparameter = None
            for hp in self.region:
                if hp.name in column_name:
                    hyperparameter: Hyperparameter = hp
                    break
            if hyperparameter is None:
                raise ValueError(f"Could not derive the hyperparameter for column {column_name}")

            if isinstance(hyperparameter, NumericHyperparameter):
                # - c : continuous hyperparameter
                self.kde_vartypes += 'c'
                self.varsizes += [0]
            else:
                # categorical hyperparameter
                if isinstance(hyperparameter, NominalHyperparameter):
                    # - u : unordered discrete hyperparameter
                    self.kde_vartypes += 'u'
                elif isinstance(hyperparameter, OrdinalHyperparameter):
                    # - o : ordered discrete hyperparameter
                    self.kde_vartypes += 'o'
                else:
                    raise TypeError(f"Unknown type of Hyperparameter: {type(hyperparameter)}")
                self.varsizes.append(len(hyperparameter.categories))

        self.varsizes = np.array(self.varsizes, dtype=int)

        # Bandwidth selection method. There are 3 possible variants:
        # 'cv_ml' - cross validation maximum likelihood
        # 'cv_ls' - cross validation the least squares, more expensive cross validation method
        # 'normal_reference' - default, quick, rule of thumb
        bw_estimation = 'normal_reference'

        good_kde = sm.nonparametric.KDEMultivariate(data=t_features_good, var_type=self.kde_vartypes, bw=bw_estimation)
        bad_kde = sm.nonparametric.KDEMultivariate(data=t_features_bad, var_type=self.kde_vartypes, bw=bw_estimation)

        good_kde.bw = np.clip(good_kde.bw, self.min_bandwidth, None)
        bad_kde.bw = np.clip(bad_kde.bw, self.min_bandwidth, None)

        self.model = {
            'good': good_kde,
            'bad': bad_kde
        }

        is_built = True
        return is_built

    def predict(self, cfg: pd.Series, transform: bool = True) -> pd.DataFrame:
        if self.model == {}:
            return pd.DataFrame()
        # Series to Dataframe
        configuration = pd.DataFrame(columns=cfg.index)
        configuration.loc[0] = cfg.values

        if transform:
            transformed_configuration = self._transform_configuration(configuration)
        else:
            transformed_configuration = configuration

        # Get accumulated probabilities for provided vectors.
        good_pdf = self.model['good'].pdf
        bad_pdf = self.model['bad'].pdf

        predicted_probability_good = max(1e-32, good_pdf(transformed_configuration))
        predicted_probability_bad = max(1e-32, bad_pdf(transformed_configuration))

        result = pd.DataFrame({self.objective["Name"] + "_probability_good": predicted_probability_good,
                               self.objective["Name"] + "_probability_bad": predicted_probability_bad}, index=[0])

        return result
