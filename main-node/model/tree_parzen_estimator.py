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

import numpy as np
import pandas as pd
import statsmodels.api as sm
from typing import MutableMapping, Mapping

from sklearn.pipeline import Pipeline

from core_entities.search_space import (
    Hyperparameter,
    NumericHyperparameter,
    NominalHyperparameter,
    OrdinalHyperparameter
)
from model.model_abs import Model
from selection.description_selection import description_selection
from preprocessing.pipelines import build_preprocessing_pipelines


class TreeParzenEstimator(Model):

    def __init__(self, parameters: MutableMapping):
        super().__init__(parameters)

        # check provided parameters:
        required_parameters = ["random_fraction", "top_n_percent", "min_bandwidth"]
        for required_parameter in required_parameters:
            if required_parameter not in self.parameters:
                raise ValueError(f"{required_parameter} was missed. Check the BRISE configuration file.")

        self.features_prp: Pipeline = None
        self.kde_vartypes = ""
        self.varsizes = []

    def build_model(
            self, features: pd.DataFrame, labels: pd.DataFrame, features_description: Mapping, is_minimization: bool
    ) -> bool:
        """
        Tries to build the new Bayesian Optimization model.
        :return: Boolean. True if the model was successfully built, otherwise - False.
        """
        self.is_built = False

        # Skip with predefined probability
        if np.random.rand() <= self.parameters["random_fraction"]:
            return self.is_built

        # 1. Check if enough data in model.
        min_points_in_model = len(features.keys()) + 1
        n_good = max(min_points_in_model, (self.parameters["top_n_percent"] * features.shape[0]) // 100)

        if len(features) < n_good * 2:
            return self.is_built

        # 2. Preprocessing for BO is predefined.
        # WARNING: If you change preprocessing you need to take care of `vartypes` specified for statsmodels KDE!
        preprocessing_parameters = {
          "OrdinalHyperparameter": "sklearn.OrdinalEncoder",
          "NominalHyperparameter": "sklearn.OrdinalEncoder",
          "IntegerHyperparameter": "sklearn.MinMaxScaler",
          "FloatHyperparameter": "sklearn.MinMaxScaler"
        }
        features_prp, labels_prp = build_preprocessing_pipelines(preprocessing_parameters, features_description)
        self.features_prp = features_prp

        t_features: pd.DataFrame = self.features_prp.fit_transform(features)

        sorted_labels = labels.sort_values(by=labels.keys()[0], ascending=is_minimization)

        t_features_good = t_features.iloc[sorted_labels[:n_good].index]
        t_features_bad = t_features.iloc[sorted_labels[n_good:].index]

        self.kde_vartypes = ""
        self.varsizes = []

        # define types of data in columns hyperparameters and, if categorical - the amount of choices it have
        for column_name in t_features.keys():
            hyperparameter = None
            for h_name in features_description:
                if h_name in column_name:
                    hyperparameter: Hyperparameter = features_description[h_name]['hyperparameter']
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
        # 'cv_ls' - cross validation least squares, more expensive crossvalidation method
        # 'normal_reference' - default, quick, rule of thumb
        bw_estimation = 'normal_reference'

        good_kde = sm.nonparametric.KDEMultivariate(data=t_features_good, var_type=self.kde_vartypes, bw=bw_estimation)
        bad_kde = sm.nonparametric.KDEMultivariate(data=t_features_bad, var_type=self.kde_vartypes, bw=bw_estimation)

        good_kde.bw = np.clip(good_kde.bw, self.parameters["min_bandwidth"], None)
        bad_kde.bw = np.clip(bad_kde.bw, self.parameters["min_bandwidth"], None)

        self.model = {
            'good': good_kde,
            'bad': bad_kde
        }

        self.is_built = True
        self.features_description = features_description
        return self.is_built

    def predict(self) -> pd.DataFrame:
        """
        Predicts the solution candidate of the model. Returns old Configuration instance if configuration is already
        exists in all_configuration list, otherwise creates new Configuration instance.
        :return
        """

        # Sampling "SamplingSize" features
        # TODO: Add sampling algorithm based on provided features (configurations)
        s_features = []
        for _ in range(self.parameters["SamplingSize"]):
            s_features.append(description_selection(self.features_description))

        t_s_features: pd.DataFrame = self.features_prp.transform(pd.DataFrame(data=s_features))

        # Get accumulated probabilities for provided vectors.
        good_pdf = self.model['good'].pdf
        bad_pdf = self.model['bad'].pdf

        # While storing prediction-related data, we should replace the information in origin columns
        ei_column_name = "TPE EI"
        c = 0
        while ei_column_name in t_s_features.keys():
            ei_column_name = "TPE EI " + str(c)
            c += 1

        # Predict probabilities of being in good or bad distribution.
        # The higher probability - more EI we have in regular BO.
        t_s_features[ei_column_name] = t_s_features.apply(
            lambda row: max(1e-32, good_pdf(row.to_numpy())) / max(1e-32, bad_pdf(row.to_numpy())),
            axis=1)

        # Applies if prediction is infinity.
        highest_finite = np.nanmax(t_s_features[ei_column_name].replace([np.inf, -np.inf], np.nan))
        is_finite = np.isfinite(t_s_features[ei_column_name])

        # This happens because some KDE ('good' or 'bad') does not contain all values for a categorical parameter.
        # As a work-around, I suggest following algorithm:
        # 1. Check if for those hyperparameters, the good_kde has a finite value:
        # (meaning, that this categories have shown to be good and we could use them.)
        #  1.2 If so - assign the highest available finite probability.
        #  1.2 If no - assign -inf. (TODO: a good idea? need to benchmark it. Other idea could be to use lowest finite).
        t_s_features.loc[- is_finite, ei_column_name] = t_s_features.drop(columns=[ei_column_name]).apply(
            lambda row: highest_finite if np.isfinite(max(1e-32, good_pdf(row.to_numpy()))) else float("-inf"),
            axis=1
        )

        # get those hyperparameters, where the EI is highest and randomly select among them
        t_s_features_highest_ei = t_s_features[t_s_features[ei_column_name] == highest_finite]
        t_prediction: pd.DataFrame = t_s_features.iloc[[np.random.choice(t_s_features_highest_ei.index)]]

        # inverse transformation to derive origin value of hyperparameters
        prediction = self.features_prp.inverse_transform(t_prediction.drop(columns=[ei_column_name]))
        return prediction
