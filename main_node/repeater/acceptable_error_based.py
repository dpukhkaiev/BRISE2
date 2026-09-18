import os
from math import exp, sqrt

from core_entities.configuration import Configuration
from repeater.repeater import Repeater
from scipy.stats import t


class AcceptableErrorBasedType(Repeater):
    """
        Repeats each Configuration until results for reach acceptable accuracy,
    the quality of each Configuration (better Configuration - better quality)
    and deviation of all Tasks are taken into account.
    """
    def __init__(self, experiment_description: dict, experiment_id: str, experiment=None):
        """
        :param experiment_description: experiment description in json format
        :param experiment_id: ID of experiment, processed by this module
        :param experiment: Experiment class instance, (!)used only in tests
        """
        super().__init__(experiment_description, experiment_id)
        # self.objectives_minimization = metric_description["TaskConfiguration"]["ObjectivesMinimization"]
        self.objectives = experiment_description["Context"]["TaskConfiguration"]["Objectives"]

        minimizations = []
        for k in self.objectives:
            minimizations.append(self.objectives[k]["Minimization"])
        self.objectives_minimization = minimizations

        self.max_tasks_per_configuration = self.repeater_configuration["Instance"]["AcceptableErrorBased"]["MaxTasksPerConfiguration"]

        if self.max_tasks_per_configuration < self.repeater_configuration["Instance"]["AcceptableErrorBased"]["MinTasksPerConfiguration"]:
            raise ValueError("Invalid configuration of the Repetition Manager provided: MaxTasksPerConfiguration(%s) "
                             "is less than MinTasksPerConfiguration(%s)!" %
                             (self.max_tasks_per_configuration, self.repeater_configuration["Instance"]["AcceptableErrorBased"]["MinTasksPerConfiguration"]))
        self.min_tasks_per_configuration = self.repeater_configuration["Instance"]["AcceptableErrorBased"]["MinTasksPerConfiguration"]

        self.base_acceptable_error = self.repeater_configuration["Instance"]["AcceptableErrorBased"]["BaseAcceptableError"]
        self.confidence_level = self.repeater_configuration["Instance"]["AcceptableErrorBased"]["ConfidenceLevel"]

        self.is_experiment_aware = False

        if "ExperimentAware" in self.repeater_configuration["Instance"]["AcceptableErrorBased"].keys():
            self.is_experiment_aware = True

        if self.is_experiment_aware:
            self.ratio_max = self.repeater_configuration["Instance"]["AcceptableErrorBased"]["ExperimentAware"]["RatioMax"]
            self.max_acceptable_error = self.repeater_configuration["Instance"]["AcceptableErrorBased"]["ExperimentAware"]["MaxAcceptableError"]
            if not self.base_acceptable_error <= self.max_acceptable_error:
                raise ValueError("Invalid Repeater configuration: some base errors values are greater that maximal errors.")

        if os.environ.get('TEST_MODE') == 'UNIT_TEST':
            self.experiment = experiment

    def evaluate(self, current_configuration: Configuration):
        """
        Return the number of evaluations to complete a configuration or 0 if it is evaluated.
        :param current_configuration: configuration under evaluation
        :return: int min_tasks_per_configuration if Configuration was not measured at all
                 or 1 if Configuration was not measured precisely or 0 if it finished
        """
        tasks_data = current_configuration.get_tasks()
        db_current_solution_record = self.database.\
            get_last_record_by_experiment_id("Experiment_state", self.experiment_id)["Current_solution"]

        c_s_results = db_current_solution_record["Results"]

        if len(tasks_data) == 0:
            return 1

        c_c_results = current_configuration.results
        c_c_results_l = []
        c_s_results_l = []
        for key in self.objectives:
            c_c_results_l.append(c_c_results[key])
            c_s_results_l.append(c_s_results[key])

        if len(tasks_data) < self.min_tasks_per_configuration:
            if self.is_experiment_aware:
                ratios = []
                for i in range(len(self.objectives_minimization)):
                    if self.objectives_minimization[i]:
                        if not c_s_results_l[i]:
                            ratio = 1
                        else:
                            ratio = c_c_results_l[i] / c_s_results_l[i]
                    else:
                        if not c_c_results_l[i]:
                            ratio = 1
                        else:
                            ratio = c_s_results_l[i] / c_c_results_l[i]
                    ratios.append(ratio)
                if all([ratio >= self.ratio_max for ratio in ratios]):
                    return 0
            return self.min_tasks_per_configuration - len(tasks_data)

        elif len(tasks_data) >= self.max_tasks_per_configuration:
            return 0
        else:
            # Calculating standard deviation
            all_dim_std = current_configuration.get_standard_deviation()

            # The number of Degrees of Freedom generally equals the number of observations (Tasks) minus
            # the number of estimated parameters.
            degrees_of_freedom = len(tasks_data) - len(c_c_results_l)/len(self.objectives)

            # Calculate the critical t-student value from the t distribution
            student_coefficients = [t.ppf(c_l, df=degrees_of_freedom) for c_l in [self.confidence_level] * len(self.objectives)]

            # Calculation of confidence interval for multiple measurements, i.e. the absolute error:
            absolute_errors = []
            for student_coefficient, dim_skd in zip(student_coefficients, all_dim_std):
                absolute_errors.append(student_coefficient * dim_skd / sqrt(len(tasks_data)))

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

                for i in range(len(self.objectives_minimization)):
                    if self.objectives_minimization[i]:
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
                        self.base_acceptable_error \
                        + (self.max_acceptable_error - self.base_acceptable_error) \
                        / (1 + exp(- (10 / self.ratio_max) * (ratio - self.ratio_max / 2)))

                    thresholds.append(adopted_threshold)

            else:
                # Or we don't adapt thresholds
                for acceptable_error in [self.base_acceptable_error] * len(self.objectives):
                    thresholds.append(acceptable_error)

            # Simple implementation of possible multi-dim Repeater decision-making:
            # If any of resulting dimensions are not accurate - just terminate.
            for threshold, error in zip(thresholds, relative_errors):
                if error > threshold:
                    return 1
            return 0
