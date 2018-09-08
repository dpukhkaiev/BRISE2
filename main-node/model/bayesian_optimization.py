import traceback

import numpy as np
# TODO: Need to uncomment it!
# import statsmodels.api as sm
import scipy.stats as sps

import logging


from model.model_abs import Model


class BayesianOptimization(Model):
    def __init__(self, whole_task_config, min_points_in_model=None, top_n_percent=15, num_samples=64, random_fraction=1/3,
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

        hps = self.self.task_config["DomainDescription"]["AllConfigurations"]

        self.kde_vartypes = ""
        self.vartypes = []

        for h in hps:
            # if hasattr(h, 'choices'):
            self.kde_vartypes += 'u'
            self.vartypes += [len(h)]
            # else:
            #     self.kde_vartypes += 'c'
            #     self.vartypes += [0]

        self.vartypes = np.array(self.vartypes, dtype=int)

        # store precomputed probs for the categorical parameters
        self.cat_probs = []

        self.configs = []
        self.losses = []
        self.good_config_rankings = dict()


    def build_model(self, result, update_model=True):
        #probability that we will pick random point
        if np.random.rand() < self.random_fraction:
            return False

        if result is None:
            # One could skip crashed results, but we decided 
            # assign a +inf loss and count them as bad configurations
            loss = np.inf
        else:
            loss = result["loss"]

        # We want to get a numerical representation of the configuration in the original space

        conf = ConfigSpace.Configuration(self.configspace, kwargs["config"])
        self.configs.append(conf.get_array())
        self.losses.append(loss)


        # skip model building:
        #a) if not enough points are available
        if len(self.configs) <= self.min_points_in_model-1:
            self.logger.debug("Only %i run(s) available, need more than %s -> can't build model!"%(len(self.configs), self.min_points_in_model+1))
            return False

        #b) during warnm starting when we feed previous results in and only update once
        if not update_model:
            return False

        train_configs = np.array(self.configs)
        train_losses =  np.array(self.losses)

        n_good= max(self.min_points_in_model, (self.top_n_percent * train_configs.shape[0])//100 )
        #n_bad = min(max(self.min_points_in_model, ((100-self.top_n_percent)*train_configs.shape[0])//100), 10)
        n_bad = max(self.min_points_in_model, ((100-self.top_n_percent)*train_configs.shape[0])//100)

        # Refit KDE for the current budget
        idx = np.argsort(train_losses)

        train_data_good = self.impute_conditional_data(train_configs[idx[:n_good]])
        train_data_bad  = self.impute_conditional_data(train_configs[idx[n_good:n_good+n_bad]])

        if train_data_good.shape[0] <= train_data_good.shape[1]:
            return False
        if train_data_bad.shape[0] <= train_data_bad.shape[1]:
            return False

        #more expensive crossvalidation method
        #bw_estimation = 'cv_ls'

        # quick rule of thumb
        bw_estimation = 'normal_reference'

        bad_kde = sm.nonparametric.KDEMultivariate(data=train_data_bad,  var_type=self.kde_vartypes, bw=bw_estimation)
        good_kde = sm.nonparametric.KDEMultivariate(data=train_data_good, var_type=self.kde_vartypes, bw=bw_estimation)

        bad_kde.bw = np.clip(bad_kde.bw, self.min_bandwidth,None)
        good_kde.bw = np.clip(good_kde.bw, self.min_bandwidth,None)

        self.model = {
        	'good': good_kde,
        	'bad' : bad_kde
        }

        # update probs for the categorical parameters for later sampling
        self.logger.debug('done building a new model based on %i/%i split\nBest loss for this budget:%f\n\n\n\n\n'%(n_good, n_bad, np.min(train_losses)))
        return True

    def validate_model(self): pass


    def predict_solution(self):

        sample = None
        info_dict = {}

        # If no model is available, sample from prior
        # also mix in a fraction of random configs

        # if self.model is None or np.random.rand() < self.random_fraction:
        #     # TODO Will use that package or new implementation?
        #     sample = self.configspace.sample_configuration()
        #     info_dict['model_based_pick'] = False

        best = np.inf
        best_vector = None

        if sample is None:
            try:
                
                l = self.model['good'].pdf
                g = self.model['bad'].pdf

                minimize_me = lambda x: max(1e-32, g(x))/max(l(x),1e-32)

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
                    for i, hp_value in enumerate(best_vector):
                        if isinstance(
                            self.configspace.get_hyperparameter(
                                self.configspace.get_hyperparameter_by_idx(i)
                            ),
                            ConfigSpace.hyperparameters.CategoricalHyperparameter
                        ):
                            best_vector[i] = int(np.rint(best_vector[i]))
                    sample = ConfigSpace.Configuration(self.configspace, vector=best_vector).get_dictionary()

                    try:
                        sample = ConfigSpace.util.deactivate_inactive_hyperparameters(
                            configuration_space=self.configspace,
                            configuration=sample
                            )
                        info_dict['model_based_pick'] = True

                    except Exception as e:
                        self.logger.warning(("="*50 + "\n")*3 +\
                            "Error converting configuration:\n%s" % sample +\
                            "\n here is a traceback:" +\
                            traceback.format_exc())
                        raise(e)

            except:
                self.logger.warning("Sampling based optimization with %i samples failed\n %s \nUsing random configuration" % (self.num_samples, traceback.format_exc()))
                sample = self.configspace.sample_configuration()
                info_dict['model_based_pick'] = False


        try:
            sample = ConfigSpace.util.deactivate_inactive_hyperparameters(
                configuration_space=self.configspace,
                configuration=sample.get_dictionary()
            ).get_dictionary()
        except Exception as e:
            self.logger.warning("Error (%s) converting configuration: %s -> "
                                "using random configuration!",
                                e,
                                sample)
            sample = self.configspace.sample_configuration().get_dictionary()
        self.logger.debug('done sampling a new configuration.')
        return sample, info_dict


    def validate_solution(self): pass

    def get_result(self): pass
