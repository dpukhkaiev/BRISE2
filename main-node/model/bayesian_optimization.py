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

import traceback
import logging
import numpy as np
import statsmodels.api as sm
import scipy.stats as sps

from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from core_entities.search_space import HyperparameterType, SearchSpace
from tools.front_API import API
from model.model_abs import Model


class BayesianOptimization(Model):

    def __init__(self, experiment: Experiment, min_points_in_model: int = None, top_n_percent: int=30,
                 random_fraction: float = 1/3, bandwidth_factor: int = 3, min_bandwidth: float = 1e-3, **kwargs):

        self.model = None
        self.top_n_percent = top_n_percent

        self.experiment = experiment
        self.isMinimizationExperiment = experiment.is_minimization()

        self.bw_factor = bandwidth_factor
        self.min_bandwidth = min_bandwidth

        if "logger" not in dir(self):
            self.logger = logging.getLogger(__name__)
        self.sub = API()

        hyperparameter_names = self.experiment.search_space.get_hyperparameter_names()
        if min_points_in_model is None:
            self.min_points_in_model = len(hyperparameter_names) + 1
        elif min_points_in_model < len(hyperparameter_names) + 1:
            self.logger.warning(f'Invalid min_points_in_model value. Setting it to {len(hyperparameter_names) + 1}')
            self.min_points_in_model = len(hyperparameter_names) + 1

        self.sampling_size = self.experiment.description["ModelConfiguration"]["SamplingSize"]
        self.random_fraction = random_fraction

        self.kde_vartypes = ""
        self.vartypes = []

        # define types of hyperparameters and, if categorical - the amount of choices it have
        for hyperparameter_name in hyperparameter_names:
            hyperparameter_type = self.experiment.search_space.get_hyperparameter_type(hyperparameter_name)
            if hyperparameter_type in (HyperparameterType.NUMERICAL_INTEGER, HyperparameterType.NUMERICAL_FLOAT):
                # TODO: need to investigate numerical integer, probably, it will be better to thread it as ordinal
                # - c : continuous hyperparameter
                self.kde_vartypes += 'c'
                self.vartypes += [0]
            else:
                # categorical hyperparameter
                self.vartypes.append(len(self.experiment.search_space.get_hyperparameter_categories(hyperparameter_name)))
                if hyperparameter_type == HyperparameterType.CATEGORICAL_NOMINAL:
                    # - u : unordered discrete hyperparameter
                    self.kde_vartypes += 'u'
                elif hyperparameter_type == HyperparameterType.CATEGORICAL_ORDINAL:
                    self.kde_vartypes += 'o'
                else:
                    self.logger.warning(f"Unknown type of Hyperparameter: {hyperparameter_type}")

        self.vartypes = np.array(self.vartypes, dtype=int)

        # Data holding fields.
        self.measured_configurations = []
        self.good_config_rankings = dict()

    def build_model(self, update_model=True):
        """
        Tries to build the new Bayesian Optimization model.
        :return: Boolean. True if the model was successfully built, otherwise - False.
        """

        # Skip model building:

        # a) With the certain probability at all (to continue with picking a random point).
        if np.random.rand() < self.random_fraction:
            # TODO refactoring: Should be generalized?..
            self.logger.info("Skipping building the model in order to pick a random configuration point.")
            return False

        # b) if not enough points are available
        if len(self.measured_configurations) <= self.min_points_in_model-1:
            self.logger.debug("Only %i run(s) available, need more than %s -> can't build model!"
                              %(len(self.measured_configurations), self.min_points_in_model+1))
            return False

        # c) during warnm starting when we feed previous results in and only update once
        # TODO: The 'warm startup' feature not implemented yet.
        if not update_model:
            return False

        self.logger.info("INFO: Building the Bayesian optimization models..")

        # TODO: works only for single objective optimization with multiple priorities. Doesn't work with classical MOO
        priorities = self.experiment.description["TaskConfiguration"]["ResultPriorities"] \
            if "ResultPriorities" in self.experiment.description["TaskConfiguration"] else [0] * \
                                        self.experiment.description["TaskConfiguration"]["ResultStructure"].__len__()
        top_priority_index = 0
        for i in range(priorities.__len__()):
            if priorities[top_priority_index] < priorities[i]:
                top_priority_index = i

        all_features = []
        all_labels = []
        # TODO: Feature encoding
        for config in self.measured_configurations:
            all_features.append(config.get_parameters_in_indexes())
            all_labels.append(config.get_average_result()[top_priority_index])

        train_features = np.array(all_features)
        train_labels = np.array(all_labels)

        n_good = max(self.min_points_in_model, (self.top_n_percent * train_features.shape[0])//100)

        n_bad = max(self.min_points_in_model, ((100-self.top_n_percent)*train_features.shape[0])//100)

        # Refit KDE for the current budget

        #TODO: argsort works not as intended for MOO
        if self.isMinimizationExperiment:
            idx = np.argsort(train_labels, axis=0)
        else:
            idx = np.argsort(-train_labels, axis=0)

        train_data_good = self.impute_conditional_data(train_features[idx[:n_good]])
        train_data_bad = self.impute_conditional_data(train_features[idx[n_good:n_good + n_bad]])

        if train_data_good.shape[0] <= train_data_good.shape[1]:
            return False
        if train_data_bad.shape[0] <= train_data_bad.shape[1]:
            return False
        if len(train_data_bad) <= self.min_points_in_model-1:
            return False
        # Bandwidth selection method. There are 3 possible variants:
        # 'cv_ml' - cross validation maximum likelihood
        # 'cv_ls' - cross validation least squares, more expensive crossvalidation method
        # 'normal_reference' - default, quick, rule of thumb
        bw_estimation = 'normal_reference'

        good_kde = sm.nonparametric.KDEMultivariate(data=train_data_good, var_type=self.kde_vartypes, bw=bw_estimation)
        bad_kde = sm.nonparametric.KDEMultivariate(data=train_data_bad,  var_type=self.kde_vartypes, bw=bw_estimation)

        self.logger.debug("The models built with bandwidth: good - %s, bad - %s. Minimum from the configurations %s"
                         % (good_kde.bw, bad_kde.bw, self.min_bandwidth))

        bad_kde.bw = np.clip(bad_kde.bw, self.min_bandwidth,None)
        good_kde.bw = np.clip(good_kde.bw, self.min_bandwidth,None)

        self.model = {
            'good': good_kde,
            'bad': bad_kde
        }

        self.logger.debug('done building a new model based on %i/%i split. Best current result:%f.'
                          %(n_good, n_bad, np.min(train_labels)))
        return True

    def validate_model(self):
        if not self.model:
            return False
        return True

    def __predict_next_configuration(self):
        """
        Predicts the solution candidate of the model. Returns old Configuration instance if configuration is already
        exists in all_configuration list, otherwise creates new Configuration instance.
        :return Configuration instance
        """
        predicted_configuration = None
        if self.isMinimizationExperiment:
            predicted_result = np.inf
        else:
            predicted_result = -np.inf
        predicted_result_vector = None

        if predicted_configuration is None:
            try:
                
                l = self.model['good'].pdf
                g = self.model['bad'].pdf

                minimize_me = lambda x: max(1e-32, g(x))/max(l(x), 1e-32)

                kde_good = self.model['good']
                kde_bad = self.model['bad']

                for i in range(self.sampling_size):
                    idx = np.random.randint(0, len(kde_good.data))
                    datum = kde_good.data[idx]
                    vector = []

                    for m, bw, t in zip(datum, kde_good.bw, self.vartypes):
                    
                        bw = max(bw, self.min_bandwidth)
                        if t == 0:
                            bw = self.bw_factor*bw
                            try:
                                vector.append(sps.truncnorm.rvs(-m/bw, (1-m)/bw, loc=m, scale=bw))
                            except:
                                self.logger.warning("Truncated Normal failed for:\ndatum=%s\nbandwidth=%s\nfor entry with value %s" % (datum, kde_good.bw, m))
                                self.logger.warning("data in the KDE:\n%s" % kde_good.data)
                        else:
                        
                            if np.random.rand() < (1-bw):
                                vector.append(int(m))
                            else:
                                vector.append(np.random.randint(t))
                    val = minimize_me(vector)

                    if not np.isfinite(val):
                        # self.logger.warning('predicted configuration vector: %s has EI value %s' % (vector, val))
                        # self.logger.warning("data in the KDEs:\n%s\n%s" %(kde_good.data, kde_bad.data))
                        # self.logger.warning("bandwidth of the KDEs:\n%s\n%s" %(kde_good.bw, kde_bad.bw))
                        # self.logger.warning("l(x) = %s" % (l(vector)))
                        # self.logger.warning("g(x) = %s" % (g(vector)))

                        # right now, this happens because a KDE does not contain all values for a categorical parameter
                        # this cannot be fixed with the statsmodels KDE, so for now, we are just going to evaluate this one
                        # if the good_kde has a finite value, i.e. there is no config with that value in the bad kde, so it shouldn't be terrible.
                        if np.isfinite(l(vector)):
                            predicted_result_vector = vector
                            break

                    if (val < predicted_result and self.isMinimizationExperiment) or (val > predicted_result and not self.isMinimizationExperiment):
                        predicted_result = val
                        predicted_result_vector = vector

                if predicted_result_vector is None:
                    self.logger.info("Sampling based optimization with %i samples failed -> using random configuration" % self.sampling_size)
                    # TODO: Check if adding random configuration selection needed. Otherwise - remove this branch.
                else:
                    # self.logger.debug('best_vector: {}, {}, {}, {}'.format(
                    #     predicted_result_vector,
                    #     predicted_result,
                    #     l(predicted_result_vector),
                    #     g(predicted_result_vector)))

                    # new configuration is sampled from the vector, provided by model
                    predicted_configuration = self.experiment.search_space.create_configuration(vector=np.asarray(predicted_result_vector))

                    # model may predict a configuation that includes forbidden combinations of values
                    # (if experiment description contains some "forbiddens"). No configuration will be sampled in this case:
                    if predicted_configuration is None:
                        raise ValueError("Predicted configuration is forbidden. It will not be added to the experiment")
                    else:
                        # check conditions for predicted configuration and disable some parameters if needed
                        # TODO: extract condition checking into separate method and do it in more elegant way
                        parameters = predicted_configuration.parameters
                        values = {}
                        for idx, param in enumerate(self.experiment.search_space.get_hyperparameter_names()):
                            values[param] = parameters[idx]
                        for param in self.experiment.search_space.get_hyperparameter_names():
                            conditions = self.experiment.search_space.get_conditions_for_hyperparameter(param)
                            for condition in conditions:
                                if values[condition] not in conditions[condition]:
                                    values[param] = None
                        for idx, param in enumerate(self.experiment.search_space.get_hyperparameter_names()):
                            parameters[idx] = values[param]
                        predicted_configuration = Configuration(parameters, Configuration.Type.PREDICTED)
            except:
                self.logger.warning("Sampling based optimization with %i samples failed\n %s\n"
                                    "Using random configuration" % (self.sampling_size, traceback.format_exc()))
                # TODO: Check if adding random configuration selection needed. Otherwise - remove this branch.

        for configuration in self.measured_configurations:
            if configuration.parameters == predicted_configuration.parameters:
                configuration.add_predicted_result(parameters=predicted_configuration.parameters,
                                                   predicted_result=[predicted_result])
                return configuration
        predicted_configuration.add_predicted_result(parameters=predicted_configuration.parameters, predicted_result=[predicted_result])

        return predicted_configuration

    def predict_next_configurations(self, amount):
        """
        Predict 'amount' Configurations that are the best (basing on a current model of the Target System).
        :param amount: int number of Configurations which will be returned.
        :return: list of Configurations that are needed to be measured.
        """

        configurations_parameters = []
        configurations = []
        while len(configurations) != amount:
            conf = self.__predict_next_configuration()

            # BO model is stochastic and could return the same Configuration several times, but we need unique ones.
            if conf.parameters not in configurations_parameters:
                configurations_parameters.append(conf.parameters)
                configurations.append(conf)
        return configurations

    def update_data(self, configurations):
        """
        Method adds configurations to whole set of configurations. Convert configurations to its indexes.

        :param configurations: List of Configuration's instances
        """
        self.measured_configurations = configurations
        for config in self.measured_configurations:
            config.add_parameters_in_indexes(config.parameters, \
                SearchSpace.extract_parameters_in_indexes_from_sub_search_space(config.parameters, self.experiment.get_current_sub_search_space()))
        return self
    
    def impute_conditional_data(self, array):

        return_array = np.empty_like(array)
        
        for i in range(array.shape[0]):
            datum = np.copy(array[i])
            nan_indices = np.argwhere(np.isnan(datum)).flatten()

            while (np.any(nan_indices)):
                nan_idx = nan_indices[0]
                valid_indices = np.argwhere(np.isfinite(array[:,nan_idx])).flatten()

                if len(valid_indices) > 0:
                    # pick one of them at random and overwrite all NaN values
                    row_idx = np.random.choice(valid_indices)
                    datum[nan_indices] = array[row_idx, nan_indices]

                else:
                    # no good point in the data has this value activated, so fill it with a valid but random value
                    t = self.vartypes[nan_idx]
                    if t == 0:
                        datum[nan_idx] = np.random.rand()
                    else:
                        datum[nan_idx] = np.random.randint(t)

                nan_indices = np.argwhere(np.isnan(datum)).flatten()
            return_array[i, :] = datum
        return return_array
