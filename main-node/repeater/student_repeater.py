from repeater.repeater_abs import Repeater
from repeater.default_repeater import DefaultRepeater
import numpy as np
from math import exp
import copy


class StudentRepeater(Repeater):
    def __init__(self, *args, **kwargs):

        # Initiating parent class and transferring WSClient in *args and other params in **kwargs
        super().__init__(*args, **kwargs)

    def decision_function(self, experiment, current_configuration, threshold=15, **configuration):
        """
        Return False while number of measurements less than max_tasks_per_configuration (inherited from abstract class).
        In other case - compute result as average between all experiments.
        :param experiment: instance of Experiment class
        :param current_configuration: a configuration under evaluation
                      shape - list, e.g. ``[1200, 32]``
        :param threshold: the maximum value of the relative error(in percents) that could be accepted.
                            Used mostly for the default configuration result
        :return: result or False
        """
        # Preparing configuration
        params = configuration.keys()

        default_configuration = configuration['default_point'] if 'default_point' in params else None

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
        configuration_object = experiment.get(current_configuration)
        average_result = []
        tasks_data = []
        if configuration_object:
            tasks_data = experiment.get(current_configuration).get_tasks()
            average_result = experiment.get(current_configuration).get_average_result()

        if len(tasks_data) < 2:
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
                threshold = 100/(1+exp(-float((average_result[index] / default_configuration[index]))+3.3))\
                            + len(tasks_data) - 2 if default_configuration else threshold + len(tasks_data)
                # If for any dimension relative error is > that threshold - abort
                if error > threshold:
                    return False

            return average_result
