from math import exp, sqrt

from core_entities.configuration import Configuration
from core_entities.experiment import Experiment
from repeater.repeater import Repeater
from scipy.stats import t


class AcceptableErrorBasedType(Repeater):
    """
        Repeats each Configuration until results for reach acceptable accuracy,
    the quality of each Configuration (better Configuration - better quality)
    and deviation of all Tasks are taken into account.
    """
    def __init__(self, experiment: Experiment, repeater_configuration: dict):
        """
        :param repeater_configuration: RepeaterConfiguration part of experiment description
        """
        super().__init__(experiment)
        self.max_tasks_per_configuration = repeater_configuration["Parameters"]["MaxTasksPerConfiguration"]

        if self.max_tasks_per_configuration < repeater_configuration["Parameters"]["MinTasksPerConfiguration"]:
            raise ValueError("Invalid configuration of Repeater provided: MinTasksPerConfiguration(%s) "
                             "is greater than ManTasksPerConfiguration(%s)!" %
                             (self.max_tasks_per_configuration, repeater_configuration["Parameters"]["MinTasksPerConfiguration"]))
        self.min_tasks_per_configuration = repeater_configuration["Parameters"]["MinTasksPerConfiguration"]

        self.base_acceptable_errors = repeater_configuration["Parameters"]["BaseAcceptableErrors"]
        self.confidence_levels = repeater_configuration["Parameters"]["ConfidenceLevels"]
        self.device_scale_accuracies = repeater_configuration["Parameters"]["DevicesScaleAccuracies"]
        self.device_accuracy_classes = repeater_configuration["Parameters"]["DevicesAccuracyClasses"]
        self.is_experiment_aware = repeater_configuration["Parameters"]["ExperimentAwareness"]["isEnabled"]

        if self.is_experiment_aware:
            self.ratios_max = repeater_configuration["Parameters"]["ExperimentAwareness"]["RatiosMax"]
            self.max_acceptable_errors = repeater_configuration["Parameters"]["ExperimentAwareness"]["MaxAcceptableErrors"]
            if not all(b_e <= m_e for b_e, m_e in zip(self.base_acceptable_errors, self.max_acceptable_errors)):
                raise ValueError("Invalid Repeater configuration: some base errors values are greater that maximal errors.")

    def evaluate(self, current_configuration: Configuration, experiment: Experiment):
        """
        Return number of measurements to finish Configuration or 0 if it finished.
        In other case - compute result as average between all experiments.
        :param current_configuration: instance of Configuration class
        :param experiment: instance of 'experiment' is required for experiment-awareness.
        :return: int min_tasks_per_configuration if Configuration was not measured at all
                 or 1 if Configuration was not measured precisely or 0 if it finished
        """
        tasks_data = current_configuration.get_tasks()

        if len(tasks_data) == 0:
            return 1

        c_c_results = current_configuration.results
        c_s_results = experiment.get_current_solution().results
        c_c_results_l = []
        c_s_results_l = []
        for key in experiment.get_objectives():
            c_c_results_l.append(c_c_results[key])
            c_s_results_l.append(c_s_results[key])

        if len(tasks_data) < self.min_tasks_per_configuration:
            if self.is_experiment_aware:
                ratios = [cur_config_dim / cur_solution_dim
                          for cur_config_dim, cur_solution_dim in zip(c_c_results_l, c_s_results_l)]
                if all([ratio >= ratio_max for ratio, ratio_max in zip(ratios, self.ratios_max)]):
                    return 0
            return self.min_tasks_per_configuration - len(tasks_data)

        elif len(tasks_data) >= self.max_tasks_per_configuration:
            return 0
        else:
            # Calculating standard deviation
            all_dim_std = current_configuration.get_standard_deviation()

            # The number of Degrees of Freedom generally equals the number of observations (Tasks) minus
            # the number of estimated parameters.
            degrees_of_freedom = len(tasks_data) - len(c_c_results_l)

            # Calculate the critical t-student value from the t distribution
            student_coefficients = [t.ppf(c_l, df=degrees_of_freedom) for c_l in self.confidence_levels]

            # Calculating confidence interval for each dimension, that contains a confidence intervals for
            # singular measurements and confidence intervals for multiple measurements.
            # First - singular measurements errors:
            conf_intervals_sm = []
            for c_l, d_s_a, d_a_c, avg in zip(self.confidence_levels, self.device_scale_accuracies,
                                              self.device_accuracy_classes, c_c_results_l):
                d = sqrt((c_l * d_s_a / 2)**2 + (d_a_c * avg/100)**2)
                conf_intervals_sm.append(c_l * d)

            # Calculation of confidence interval for multiple measurements:
            conf_intervals_mm = []
            for student_coefficient, dim_skd in zip(student_coefficients, all_dim_std):
                conf_intervals_mm.append(student_coefficient * dim_skd / sqrt(len(tasks_data)))

            # confidence interval, or in other words absolute error
            absolute_errors = []
            for c_i_ss, c_i_mm in zip(conf_intervals_sm, conf_intervals_mm):
                absolute_errors.append(sqrt(pow(c_i_ss, 2) + pow(c_i_mm, 2)))

            # Calculating relative error for each dimension
            relative_errors = []
            for interval, avg_res in zip(absolute_errors, c_c_results_l):
                if not avg_res:     # it is 0 or 0.0
                    # if new use-cases appear with the same behaviour.
                    if interval == 0:
                        avg_res = 1  # Anyway relative error will be 0 and avg will not be changed.
                    else:
                        return 1
                relative_errors.append(interval / avg_res * 100)

            # Thresholds for relative errors that should not be exceeded for accurate measurement.
            thresholds = []
            if self.is_experiment_aware:
                # We adapt thresholds
                objectives_minimization = experiment.get_objectives_minimization()

                for i in range(len(objectives_minimization)):
                    if objectives_minimization[i]:
                        if not c_s_results_l[i]:
                            ratio = 1
                        else:
                            ratio = c_c_results_l[i] / c_s_results_l[i]
                    else:
                        if not c_c_results_l[i]:
                            ratio = 1
                        else:
                            ratio = c_s_results_l[i] / c_c_results_l[i]

                    adopted_threshold = \
                        self.base_acceptable_errors[i] \
                        + (self.max_acceptable_errors[i] - self.base_acceptable_errors[i]) \
                        / (1 + exp(- (10 / self.ratios_max[i]) * (ratio - self.ratios_max[i] / 2)))

                    thresholds.append(adopted_threshold)

            else:
                # Or we don't adapt thresholds
                for acceptable_error in self.base_acceptable_errors:
                    thresholds.append(acceptable_error)

            # Simple implementation of possible multi-dim Repeater decision making:
            # If any of resulting dimensions are not accurate - just terminate.
            for threshold, error in zip(thresholds, relative_errors):
                if error > threshold:
                    return 1
            return 0
