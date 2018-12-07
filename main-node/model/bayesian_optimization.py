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

import numpy as np
import statsmodels.api as sm
import scipy.stats as sps

import logging

from core_entities.configuration import Configuration
from tools.front_API import API

from model.model_abs import Model


class BayesianOptimization(Model):
# TODO: need to implement Maximization/minimization model.

    def __init__(self, experiment_description, min_points_in_model=None, top_n_percent=30, num_samples=96,
                 random_fraction=1/3, bandwidth_factor=3, min_bandwidth=1e-3, **kwargs):

        self.model = None
        self.top_n_percent = top_n_percent

        # 'ExperimentsConfiguration', 'ModelConfiguration', 'DomainDescription', 'SelectionAlgorithm'
        self.experiment_description = experiment_description

        self.bw_factor = bandwidth_factor
        self.min_bandwidth = min_bandwidth

        if "logger" not in dir(self):
            self.logger = logging.getLogger(__name__)
        # Send updates to subscribers
        self.sub = API()

        if min_points_in_model is None:
            self.min_points_in_model = len(self.experiment_description["DomainDescription"]["AllConfigurations"])+1
        elif min_points_in_model < len(self.experiment_description["DomainDescription"]["AllConfigurations"])+1:
            self.logger.warning('Invalid min_points_in_model value. Setting it to %i' % (
                len(self.experiment_description["DomainDescription"]["AllConfigurations"])+1))
            self.min_points_in_model = len(self.experiment_description["DomainDescription"]["AllConfigurations"])+1

        self.num_samples = num_samples
        self.random_fraction = random_fraction

        hps = self.experiment_description["DomainDescription"]["AllConfigurations"]

        self.kde_vartypes = ""
        self.vartypes = []

        for h in hps:
            # Ordered, cause our data is ordered, possible variants:
            #             - c : continuous
            #             - u : unordered (discrete)
            #             - o : ordered (discrete)
            self.kde_vartypes += 'u'
            self.vartypes += [len(h)]

        self.vartypes = np.array(self.vartypes, dtype=int)

        # store precomputed probs for the categorical parameters
        self.cat_probs = []

        # Data holding fields.
        self.all_configurations = []
        self.solution_configuration = []
        self.good_config_rankings = dict()

    def _config_to_idx(self, configuration):
        """
        Helper function to convert real configuration to its indexes in the search space.
        :param configuration: List. Target system configurations.
        :return: List. Indexes (integers).
        """
        configuration_in_indexes = []

        for hyperparam_index, value in enumerate(configuration):
            param_index = self.experiment_description["DomainDescription"]["AllConfigurations"][hyperparam_index].index(value)
            configuration_in_indexes.insert(hyperparam_index, param_index)

        return configuration_in_indexes

    def build_model(self, update_model=True):
        """
        Tries to build the new Bayesian Optimization model.
        :return: Boolean. True if the model was successfully built, otherwise - False.
        """

        # Skip model building:

        # a) With the certain probability at all (to continue with picking a random point).
        if np.random.rand() < self.random_fraction:
            self.logger.info("Skipping building the model in order to pick a random configuration point.")
            return False

        # b) if not enough points are available
        if len(self.all_configurations) <= self.min_points_in_model-1:
            self.logger.debug("Only %i run(s) available, need more than %s -> can't build model!"%(len(self.all_configurations), self.min_points_in_model+1))
            return False

        # c) during warnm starting when we feed previous results in and only update once
        # TODO: The 'warm startup' feature not implemented yet.
        if not update_model:
            return False

        self.logger.info("INFO: Building the Bayesian optimization models..")

        all_features = []
        all_labels = []
        for config in self.all_configurations:
            all_features.append(config.configuration_in_indexes)
            all_labels.append(config.average_result)

        train_features = np.array(all_features)
        train_labels = np.array(all_labels)

        n_good = max(self.min_points_in_model, (self.top_n_percent * train_features.shape[0])//100)
        n_bad = max(self.min_points_in_model, ((100-self.top_n_percent)*train_features.shape[0])//100)

        # Refit KDE for the current budget
        idx = np.argsort(train_labels, axis=0)

        train_data_good = self.impute_conditional_data(train_features[idx[:n_good]])
        train_data_bad = self.impute_conditional_data(train_features[idx[n_good:n_good+n_bad]])

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

        self.logger.info("The models built with bandwidth: good - %s, bad - %s. Minimum from the configurations %s"
                         % (good_kde.bw, bad_kde.bw, self.min_bandwidth))

        bad_kde.bw = np.clip(bad_kde.bw, self.min_bandwidth,None)
        good_kde.bw = np.clip(good_kde.bw, self.min_bandwidth,None)

        self.model = {
            'good': good_kde,
            'bad': bad_kde
        }

        # update probs for the categorical parameters for later sampling
        self.logger.debug('done building a new model based on %i/%i split\nBest current result:%f\n\n\n\n\n'
                          %(n_good, n_bad, np.min(train_labels)))
        return True

    def validate_model(self, search_space):
        #TODO how validate
        # Check if model was built.
        if not self.model:
            return False
        return True

    def predict_solution(self):
        """
        Predicts the solution candidate of the model. Returns old Configuration instance if configuration is already
        exists in all_configuration list, otherwise creates new Configuration instance.
        :return Configuration instance
        """
        predicted_configuration = None
        info_dict = {}

        predicted_result = np.inf
        predicted_result_vector = None

        if predicted_configuration is None:
            try:
                
                l = self.model['good'].pdf
                g = self.model['bad'].pdf
                #TODO test max_me
                minimize_me = lambda x: max(1e-32, g(x))/max(l(x), 1e-32)

                kde_good = self.model['good']
                kde_bad = self.model['bad']

                for i in range(self.num_samples):
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
                        self.logger.warning('predicted configuration vector: %s has EI value %s' % (vector, val))
                        self.logger.warning("data in the KDEs:\n%s\n%s" %(kde_good.data, kde_bad.data))
                        self.logger.warning("bandwidth of the KDEs:\n%s\n%s" %(kde_good.bw, kde_bad.bw))
                        self.logger.warning("l(x) = %s" % (l(vector)))
                        self.logger.warning("g(x) = %s" % (g(vector)))

                        # right now, this happens because a KDE does not contain all values for a categorical parameter
                        # this cannot be fixed with the statsmodels KDE, so for now, we are just going to evaluate this one
                        # if the good_kde has a finite value, i.e. there is no config with that value in the bad kde, so it shouldn't be terrible.
                        if np.isfinite(l(vector)):
                            predicted_result_vector = vector
                            break

                    if val < predicted_result:
                        predicted_result = val
                        predicted_result_vector = vector

                if predicted_result_vector is None:
                    self.logger.info("Sampling based optimization with %i samples failed -> using random configuration" % self.num_samples)
                    # TODO: Check if adding random configuration selection needed. Otherwise - remove this branch.
                    info_dict['model_based_pick'] = False
                else:
                    self.logger.debug('best_vector: {}, {}, {}, {}'.format(
                        predicted_result_vector,
                        predicted_result,
                        l(predicted_result_vector),
                        g(predicted_result_vector)))

                    predicted_configuration = []
                    for index, dimension in enumerate(self.experiment_description["DomainDescription"]["AllConfigurations"]):
                        predicted_configuration.append(dimension[predicted_result_vector[index]])

            except:
                self.logger.warning("Sampling based optimization with %i samples failed\n %s\n"
                                    "Using random configuration" % (self.num_samples, traceback.format_exc()))
                # TODO: Check if adding random configuration selection needed. Otherwise - remove this branch.
                info_dict['model_based_pick'] = False

        self.logger.debug('done sampling a new configuration.')
        for configuration in self.all_configurations:
            if configuration.configuration == predicted_configuration:
                configuration.add_predicted_result(configuration=predicted_configuration, predicted_result=[predicted_result])
                return configuration
        predicted_configuration_class = Configuration(predicted_configuration)
        predicted_configuration_class.add_predicted_result(configuration=predicted_configuration, predicted_result=[predicted_result])
        return predicted_configuration_class

    def get_result(self, repeater):
        # TODO: need to review a way of features and labels addition here.
        #   In case, if the model predicted the final point, that has less value, than the default, but there is
        # a point, that has less value, than the predicted point - report this point instead of predicted point.
        self.logger.info("\n\nFinal report:")

        if self.solution_configuration == []:
            self.solution_configuration = [self.all_configurations[0]]
            for configuration in self.all_configurations:
                if configuration < self.solution_configuration[0]:
                    self.solution_configuration = [configuration]
            self.logger.info("Optimal configuration was not found. Reporting best of the measured.")
            self.sub.send('log', 'info', message="Optimal configuration was not found. Configuration: %s, Quality: %s" %
                          (self.solution_configuration[0].configuration, self.solution_configuration[0].average_result))
        else:
            min_configuration = [self.all_configurations[0]]
            for configuration in self.all_configurations:
                if configuration < min_configuration[0]:
                    min_configuration = [configuration]

            if min_configuration[0] < self.solution_configuration[0]:
                temp_message = ("Configuration: %s, Quality: %s, "
                      "that model gave worse that one of measured previously, but better than default."
                      "Reporting best of measured." % (self.solution_configuration[0].configuration,
                                                       self.solution_configuration[0].average_result))
                self.logger.info(temp_message)
                self.sub.send('log', 'info', message=temp_message)
                self.solution_configuration = min_configuration

        self.logger.info("ALL MEASURED CONFIGURATIONS:")
        for configuration in self.all_configurations:
            self.logger.info("%s: %s" % (str(configuration.configuration), str(configuration.average_result)))
        self.logger.info("Number of measured points: %s" % len(self.all_configurations))
        self.logger.info("Number of performed measurements: %s" % repeater.performed_measurements)
        self.logger.info("Best found energy: %s, with configuration: %s"
                         % (self.solution_configuration[0].average_result,
                            self.solution_configuration[0].configuration))

        all_features = []
        for configuration in self.all_configurations:
            all_features.append(configuration.configuration)
        self.sub.send('final', 'configuration',
                      configurations=[self.solution_configuration[0].configuration],
                      results=[self.solution_configuration[0].average_result],
                      type=['bayesian solution'],
                      measured_points=[all_features],
                      performed_measurements=[repeater.performed_measurements])

        return self.solution_configuration

    def add_data(self, configurations):
        """
        Method adds configurations to whole set of configurations. Convert configurations to its indexes.

        :param configurations: List of Configuration's instances
        """
        self.all_configurations = configurations
        for config in self.all_configurations:
            config.configuration_in_indexes = self._config_to_idx(config.configuration)
    
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
            return_array[i,:] = datum
        return(return_array)
