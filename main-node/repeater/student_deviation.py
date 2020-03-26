import numpy as np
from math import exp, sqrt
from scipy.stats import t

from repeater.default import DefaultType
from core_entities.configuration import Configuration
from core_entities.experiment import Experiment


class StudentDeviationType(DefaultType):
    """
        Repeats each Configuration until results for reach acceptable accuracy,
    the quality of each Configuration (better Configuration - better quality)
    and deviation of all Tasks are taken into account.
    """
    def __init__(self, repeater_configuration: dict):
        """
        :param repeater_configuration: RepeaterConfiguration part of experiment description
        """
        super().__init__(repeater_configuration)

        if self.max_tasks_per_configuration < repeater_configuration["MinTasksPerConfiguration"]:
            raise ValueError("Invalid configuration of Repeater provided: MinTasksPerConfiguration(%s) "
                             "is greater than ManTasksPerConfiguration(%s)!" %
                             (self.max_tasks_per_configuration, repeater_configuration["MinTasksPerConfiguration"]))
        self.min_tasks_per_configuration = repeater_configuration["MinTasksPerConfiguration"]

        self.base_acceptable_errors = repeater_configuration["BaseAcceptableErrors"]
        self.confidence_levels = repeater_configuration["ConfidenceLevels"]
        self.device_scale_accuracies = repeater_configuration["DevicesScaleAccuracies"]
        self.device_accuracy_classes = repeater_configuration["DevicesAccuracyClasses"]
        self.is_experiment_aware = repeater_configuration["ExperimentAwareness"]["isEnabled"]

        if self.is_experiment_aware:
            self.ratios_max = repeater_configuration["ExperimentAwareness"]["RatiosMax"]
            self.max_acceptable_errors = repeater_configuration["ExperimentAwareness"]["MaxAcceptableErrors"]
            if not all(b_e <= m_e for b_e, m_e in zip(self.base_acceptable_errors, self.max_acceptable_errors)):
                raise ValueError("Invalid Repeater configuration: some base errors values are greater that maximal errors.")

    def evaluate(self, current_configuration: Configuration, experiment: Experiment):
        """
        Return number of measurements to finish Configuration or 0 if it finished.
        In other case - compute result as average between all experiments.
        :param current_configuration: instance of Configuration class
        :param experiment: instance of 'experiment' is required for experiment-awareness.
        :return: int min_tasks_per_configuration if Configuration was not measured at all or 1 if Configuration was not measured precisely or 0 if it finished
        """
        tasks_data = current_configuration.get_tasks()
        average_result = current_configuration.get_average_result()
        current_solution = experiment.get_current_solution().get_average_result()

        if len(tasks_data) == 0:
            return 1

        elif len(tasks_data) < self.min_tasks_per_configuration:
            if self.is_experiment_aware:
                ratios = [cur_config_dim / cur_solution_dim for cur_config_dim, cur_solution_dim in zip(average_result, current_solution)]
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
            degrees_of_freedom = len(tasks_data) - len(average_result)

            # Calculate the critical t-student value from the t distribution
            student_coefficients = [t.ppf(c_l, df=degrees_of_freedom) for c_l in self.confidence_levels]

            # Calculating confidence interval for each dimension, that contains a confidence intervals for
            # singular measurements and confidence intervals for multiple measurements.
            # First - singular measurements errors:
            conf_intervals_sm = []
            for c_l, d_s_a, d_a_c, avg in zip(self.confidence_levels, self.device_scale_accuracies, self.device_accuracy_classes, average_result):
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
            for interval, avg_res in zip(absolute_errors, average_result):
                if not avg_res:     # it is 0 or 0.0
                    # TODO: WorkAround for cases where avg = 0, need to review it here and in \ratio\ calculation
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
                minimization_experiment = experiment.is_minimization()

                for b_t, max_t, r_max, avg_res, cur_solution_avg in \
                        zip(self.base_acceptable_errors, self.max_acceptable_errors, self.ratios_max, average_result, current_solution):
                    if minimization_experiment:
                        if not cur_solution_avg:
                            ratio = 1
                        else:
                            ratio = avg_res / cur_solution_avg
                    else:
                        if not avg_res:
                            ratio = 1
                        else:
                            ratio = cur_solution_avg / avg_res

                    adopted_threshold = b_t + (max_t - b_t) / (1 + exp(- (10 / r_max) * (ratio - r_max/2)))
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
