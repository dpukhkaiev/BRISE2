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
# TODO: Need to uncomment it!
import statsmodels.api as sm
import scipy.stats as sps

import logging


from model.model_abs import Model


class BayesianOptimization(Model):

    def __init__(self, whole_task_config, min_points_in_model=None, top_n_percent=30, num_samples=96, random_fraction=1/3,
                 bandwidth_factor=3, min_bandwidth=1e-3, **kwargs):

        self.model = None
        self.top_n_percent = top_n_percent

        # 'ExperimentsConfiguration', 'ModelConfiguration', 'DomainDescription', 'SelectionAlgorithm'
        self.task_config = whole_task_config

        self.bw_factor = bandwidth_factor
        self.min_bandwidth = min_bandwidth

        if "logger" not in dir(self):
            self.logger = logging.getLogger(__name__)

        if min_points_in_model is None:
            self.min_points_in_model = len(self.task_config["DomainDescription"]["AllConfigurations"])+1
        elif min_points_in_model < len(self.task_config["DomainDescription"]["AllConfigurations"])+1:
            self.logger.warning('Invalid min_points_in_model value. Setting it to %i' % (
                len(self.task_config["DomainDescription"]["AllConfigurations"])+1))
            self.min_points_in_model = len(self.task_config["DomainDescription"]["AllConfigurations"])+1

        self.num_samples = num_samples
        self.random_fraction = random_fraction

        hps = self.task_config["DomainDescription"]["AllConfigurations"]

        self.kde_vartypes = ""
        self.vartypes = []

        for h in hps:
            # if hasattr(h, 'choices'):
            # Ordered, cause our data is ordered, possible variants:
            #             - c : continuous
            #             - u : unordered (discrete)
            #             - o : ordered (discrete)
            self.kde_vartypes += 'u'
            self.vartypes += [len(h)]
            # else:
            #     self.kde_vartypes += 'c'
            #     self.vartypes += [0]

        self.vartypes = np.array(self.vartypes, dtype=int)

        # store precomputed probs for the categorical parameters
        self.cat_probs = []

        # Data holding fields.
        self.all_features = []
        self.all_labels = []
        self.solution_features = []
        self.solution_labels = []
        self.good_config_rankings = dict()

    def _idx_to_config(self, indexes):
        """
        Helper function to transform list of indexes in search space of configurations to the real configurations
        :param indexes: List. indexes (integers)
        :return: List. Target system configurations.
        """
        configurations = []

        for cur_index in indexes:
            configuration = []
            for hyperparam_index, index in enumerate(cur_index):
                hyperparam_value = self.task_config["DomainDescription"]["AllConfigurations"][hyperparam_index][index]
                configuration.insert(hyperparam_index, hyperparam_value)
            configurations.append(configuration)

        return configurations

    def _config_to_idx(self, configs):
        """
        Helper function to real configuration to its indexes in the search space.
        :param config: List. Target system configurations.
        :return: List. Indexes (integers).
        """
        indexes = []

        for config in configs:
            cur_indexes = []
            for hyperparam_index, value in enumerate(config):
                param_index = self.task_config["DomainDescription"]["AllConfigurations"][hyperparam_index].index(value)
                cur_indexes.insert(hyperparam_index, param_index)
            indexes.append(cur_indexes)

        return indexes

    def build_model(self, update_model=True):
        """

        Tries to build the new Bayesian Optimization model.

        :return: Boolean. True if the model was successfully built, otherwise - False.
        """

        # Skip model building:

        # a) With the certain probability at all (to continue with picking a random point).
        if np.random.rand() < self.random_fraction:
            print("INFO: Skipping building the model in order to pick a random configuration point.")
            return False

        # b) if not enough points are available
        if len(self.all_features) <= self.min_points_in_model-1:
            self.logger.debug("Only %i run(s) available, need more than %s -> can't build model!"%(len(self.all_features), self.min_points_in_model+1))
            return False

        # c) during warnm starting when we feed previous results in and only update once
        # TODO: The 'warm startup' feature not implemented yet.
        if not update_model:
            return False

        print("INFO: Building the Bayesian optimization models..")

        train_features = np.array(self.all_features)
        train_labels = np.array(self.all_labels)

        n_good = max(self.min_points_in_model, (self.top_n_percent * train_features.shape[0])//100)
        # n_bad = min(max(self.min_points_in_model, ((100-self.top_n_percent)*train_features.shape[0])//100), 10)
        n_bad = max(self.min_points_in_model, ((100-self.top_n_percent)*train_features.shape[0])//100)

        # Refit KDE for the current budget
        idx = np.argsort(train_labels, axis=0)

        train_data_good = self.impute_conditional_data(train_features[idx[:n_good]])
        train_data_bad  = self.impute_conditional_data(train_features[idx[n_good:n_good+n_bad]])

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
        

        print("INFO: The models built with bandwidth: good - %s, bad - %s. Minimum from the configurations %s"
              % (good_kde.bw, bad_kde.bw, self.min_bandwidth))

        bad_kde.bw = np.clip(bad_kde.bw, self.min_bandwidth,None)
        good_kde.bw = np.clip(good_kde.bw, self.min_bandwidth,None)

        self.model = {
            'good': good_kde,
            'bad' : bad_kde
        }

        # update probs for the categorical parameters for later sampling
        self.logger.debug('done building a new model based on %i/%i split\nBest loss for this budget:%f\n\n\n\n\n'%(n_good, n_bad, np.min(train_labels)))
        return True

    def validate_model(self, io, search_space):
        #TODO how validate
        # Check if model was built.
        if not self.model:
            return False
        return True


    def predict_solution(self, io, search_space):

        sample = None
        info_dict = {}

        best = np.inf
        best_vector = None

        if sample is None:
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
                        self.logger.warning('sampled vector: %s has EI value %s' % (vector, val))
                        self.logger.warning("data in the KDEs:\n%s\n%s" %(kde_good.data, kde_bad.data))
                        self.logger.warning("bandwidth of the KDEs:\n%s\n%s" %(kde_good.bw, kde_bad.bw))
                        self.logger.warning("l(x) = %s" % (l(vector)))
                        self.logger.warning("g(x) = %s" % (g(vector)))

                        # right now, this happens because a KDE does not contain all values for a categorical parameter
                        # this cannot be fixed with the statsmodels KDE, so for now, we are just going to evaluate this one
                        # if the good_kde has a finite value, i.e. there is no config with that value in the bad kde, so it shouldn't be terrible.
                        if np.isfinite(l(vector)):
                            best_vector = vector
                            break

                    if val < best:
                        best = val
                        best_vector = vector

                if best_vector is None:
                    self.logger.debug("Sampling based optimization with %i samples failed -> using random configuration" % self.num_samples)
                    sample = self.configspace.sample_configuration().get_dictionary()
                    info_dict['model_based_pick'] = False
                else:
                    self.logger.debug('best_vector: {}, {}, {}, {}'.format(best_vector, best, l(best_vector), g(best_vector)))
                    sample = []
                    for index, dimension in enumerate(self.task_config["DomainDescription"]["AllConfigurations"]):
                        sample.append(dimension[best_vector[index]])

            except:
                self.logger.warning("Sampling based optimization with %i samples failed\n %s \nUsing random configuration" % (self.num_samples, traceback.format_exc()))
                # sample = self.configspace.sample_configuration()
                info_dict['model_based_pick'] = False


        self.logger.debug('done sampling a new configuration.')
        return [best], sample


    def validate_solution(self, io, task_config, repeater, default_value, predicted_features):
        # validate() in regression
        print("Verifying solution that model gave..")
        if io:
            io.emit('info', {'message': "Verifying solution that model gave.."})
        solution_candidate = repeater.measure_task([predicted_features], io=io)
        solution_feature = predicted_features
        solution_labels = solution_candidate
        # If our measured energy higher than default best value - add this point to data set and rebuild model.
        #validate false
        if solution_labels >= default_value:
            print("Predicted energy largeror equal default: %s >= %s" % (solution_labels[0][0], default_value[0][0]))
            prediction_is_final = False
        else:
            print("Solution validation success!")
            if io:
                io.emit('info', {'message': "Solution validation success!"})
            prediction_is_final = True
        self.solution_labels = solution_labels[0]
        self.solution_features = solution_feature[0]
        return self.solution_labels, prediction_is_final

    def get_result(self, repeater, io):
        # TODO: need to review a way of features and labels addition here.
        #   In case, if regression predicted final point, that have less energy consumption, that default, but there is
        # point, that have less energy consumption, that predicted - report this point instead predicted.
        maximize_done = False
        print("\n\nFinal report:")

        if not self.solution_labels:
            temp_message = "Optimal configuration was not found. Reporting best of the measured."
            print(temp_message)
            self.solution_labels = min(self.all_labels)
            index_of_the_best_labels = self.all_labels.index(self.solution_labels)
            if not self.task_config['ModelConfiguration']['MinimizationTask'] and not maximize_done:
                self.solution_labels[0] = 1 - self.solution_labels[0]
                maximize_done = True
            self.solution_features = [] 
            for i in range(len(self.all_features[index_of_the_best_labels])):
                self.solution_features.append(self.task_config['DomainDescription']['AllConfigurations'][i][self.all_features[index_of_the_best_labels][i]])
            if io:
                io.emit('info', {'message': temp_message, "quality": self.solution_labels, "conf": self.solution_features})

        elif min(self.all_labels) < self.solution_labels:
            self.solution_labels = min(self.all_labels)
            index_of_the_best_labels = self.all_labels.index(self.solution_labels)
            if not self.task_config['ModelConfiguration']['MinimizationTask'] and not maximize_done:
                self.solution_labels[0] = 1 - self.solution_labels[0]
                maximize_done = True
            self.solution_features = [] 
            for i in range(len(self.all_features[index_of_the_best_labels])):
                self.solution_features.append(self.task_config['DomainDescription']['AllConfigurations'][i][self.all_features[index_of_the_best_labels][i]])
            temp_message = ("Configuration(%s) quality(%s), "
                  "\nthat model gave worse that one of measured previously, but better than default."
                  "\nReporting best of measured." %
                  (self.solution_features, self.solution_labels))
            print(temp_message)
            if io:
                io.emit('info', {'message': temp_message, "quality": self.solution_labels, "conf": self.solution_features})
        if not self.task_config['ModelConfiguration']['MinimizationTask'] and not maximize_done:
                self.solution_labels = min(self.all_labels)
                maximize_done = True

        print("ALL MEASURED FEATURES:\n%s" % str(self.all_features))
        print("ALL MEASURED LABELS:\n%s" % str(self.all_labels))
        print("Number of measured points: %s" % len(self.all_features))
        print("Number of performed measurements: %s" % repeater.performed_measurements)
        print("Best found value: %s, with configuration: %s" % (self.solution_labels, self.solution_features))

        if io:
            temp = {"best point": {'configuration': self.solution_features, 
                    "result": self.solution_labels, 
                    "measured points": len(self.all_features),
                    'performed measurements': repeater.performed_measurements}
                    }
            io.emit('best point', temp)

        return self.solution_labels, self.solution_features

    def add_data(self, features, labels): 
        """
        
        Method adds new features and labels to whole set of features and labels.

        :param features: List. features in machine learning meaning selected by Sobol
        :param labels: List. labels in machine learning meaning selected by Sobol
        """
        # An input validation and updating of the features and labels set.
        # 1. Tests if lists of features and labels are same length.
        # 2. Tests if all lists are nested.
        # 3. Tests if all values of nested fields are ints or floats. (Because regression works only with those data).
        # These all(all(...)..) returns true if all data
        try:

            assert len(features) == len(labels) > 0, \
                "Incorrect length!\nFeatures:%s\nLabels:%s" % (str(features), str(labels))

            assert all(all(isinstance(value, (int, float, str)) for value in feature) for feature in features), \
                "Incorrect data types in features: %s" % str(features)

            assert all(all(isinstance(value, (int, float, str)) for value in label) for label in labels), \
                "Incorrect data types in labelss: %s" % str(labels)
            if labels is None:
                # One could skip crashed results, but we decided 
                # assign a +inf loss and count them as bad configurations
                self.all_labels += np.inf
            else:
                self.all_features += self._config_to_idx(features)
                self.all_labels += labels

        except AssertionError as err:
            # TODO: replace with logger.
            print("ERROR! Regression input validation error:\n%s" % err)
    
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
