import numpy as np
from math import exp


class StudentJudge:
    """
        Repeats each Configuration until results for reach acceptable accuracy,
    the quality of each Configuration (better Configuration - better quality)
    and deviation of all Tasks are taken into account.
    """
    def __init__(self, repeater_configuration: dict):
        """
        :param repeater_configuration: RepeaterConfiguration part of experiment description
        """
        self.max_tasks_per_configuration = repeater_configuration["MaxTasksPerConfiguration"]

        if self.max_tasks_per_configuration < repeater_configuration["MinTasksPerConfiguration"]:
            raise ValueError("Invalid configuration of Repeater provided: MinTasksPerConfiguration(%s) "
                             "is greater than ManTasksPerConfiguration(%s)!" %
                             (self.max_tasks_per_configuration, repeater_configuration["MinTasksPerConfiguration"]))
        self.min_tasks_per_configuration = repeater_configuration["MinTasksPerConfiguration"]

    def verdict(self, current_configuration, threshold=15, **params):
        """
        Return False while number of measurements less than max_tasks_per_configuration (inherited from abstract class).
        In other case - compute result as average between all experiments.
        :param current_configuration: instance of Configuration class
        :param threshold: the maximum value of the relative error(in percents) that could be accepted.
                            Used mostly for the default configuration result
        :return: result or False
        """
        # Preparing configuration
        if 'current_solution' in params.keys():
            current_solution = params['current_solution'][0].get_average_result()
        else:
            current_solution = None

        # For trusted probability 0.95
        student_coefficients = {
            2: 12.7,
            3: 4.30,
            4: 3.18,
            5: 2.78,
            6: 2.57,
            7: 2.45,
            8: 2.36,
            9: 2.31,
            10: 2.26,
            11: 1.96
        }

        # first of all - need at least 2 measurements
        average_result = []
        tasks_data = []
        if current_configuration:
            tasks_data = current_configuration.get_tasks()
            average_result = current_configuration.get_average_result()

        if len(tasks_data) < self.min_tasks_per_configuration:
            return False

        elif len(tasks_data) >= self.max_tasks_per_configuration:
            return average_result

        else:
            # Calculating average for all dimensions
            configuration_results = []
            for key, key_dict in tasks_data.items():
                configuration_results.append(key_dict["result"])

            configuration_results_np = np.matrix(configuration_results)

            # Calculating standard deviation
            all_dim_sko = np.std(configuration_results_np, axis=0)

            # Pick the Student's coefficient, if number of experiments is 11 or more - pick coefficient for 11
            student_coefficient = student_coefficients[len(tasks_data) if len(tasks_data) < 11 else 11]

            # Calculating confidence interval for each dimension
            conf_interval = [student_coefficient * dim_sko / pow(len(tasks_data), 0.5) for dim_sko in all_dim_sko]

            # Calculating relative error for each dimension
            relative_errors = [interval / avg * 100 for interval, avg in zip(conf_interval, average_result)][0].tolist()[0]

            # Verifying that deviation of errors in each dimension is
            for index, error in enumerate(relative_errors):
                # Selecting needed threshold - 100/(1+exp(-x+3.3)) where x is value of measured point divided to default
                threshold = 100/(1+exp(-float((average_result[index] / current_solution[index]))+3.3))\
                            + len(tasks_data) - 2 if current_solution else threshold + len(tasks_data)
                # If for any dimension relative error is > that threshold - abort
                if error > threshold:
                    return False

            return average_result
