import logging


class Configuration:

    def __init__(self, configuration):
        self.logger = logging.getLogger(__name__)
        # The shape of configuration - list, e.g.
        #                              [2900.0, 32]
        self.configuration = configuration
        self.configuration_in_indexes = []

        # The shape of data - dict, e.g.
        #                     {
        #                        id_task_1: {
        #                           "result": result,
        #                           "worker": worker_name
        #                        }
        #                        id_task_1: {
        #                          "result": result,
        #                          "worker": worker_name
        #                        }
        #                        ...
        #                     }
        # The shape of id_task_1 - int
        # The shape of result - list with one value, e.g.
        #                       [700.56]
        # The shape of worker_name - string
        self.data = {}

        # The shape of average_result - list with one average value of 'result' fields in 'data', e.g.
        #                               [806.43]
        self.average_result = []

        self.predicted_result = []

    def add_predicted_result(self, configuration, predicted_result):

        if self.configuration == configuration:
            self.predicted_result = predicted_result

    def add_data(self, configuration, task_id=None, result=None, worker=None):

        if self.configuration == configuration:
            if task_id and result and worker:
                self.data[task_id] = {
                    "result": result,
                    "worker": worker
                }
                self.calculate_average_result()
        else:
            self.logger.error('New configuration %s does not match with current configuration %s'
                              % (configuration, self.configuration), exc_info=True)

    def get_data(self):
        return self.data

    def get_average_result(self):
        return self.average_result

    def __lt__(self, compared_configuration):
        """
        Returns True, if 'self' < 'compared_configuration'. Otherwise - False
        :param compared_configuration: instance of Configuration class
        :return: True or False
        """
        return self.average_result[0] < compared_configuration.average_result[0]

    def __gt__(self, compared_configuration):
        """
        Returns True, if 'self' > 'compared_configuration'. Otherwise - False
        :param compared_configuration: instance of Configuration class
        :return: True or False
        """
        return compared_configuration.__lt__(self)

    def calculate_average_result(self):
        """
         Calculating average result for configuration
        """
        # create a list
        average_result_length = 0
        for sub_dictionary_key, sub_dictionary in self.data.items():
            average_result_length = len(sub_dictionary["result"])
            break
        self.average_result = [0 for x in range(average_result_length)]

        for key, key_dict in self.data.items():
            for index, value in enumerate(key_dict["result"]):
                # If the result doesn't have digital values, these values should be assigned  to the result variable
                # without averaging
                if type(value) not in [int, float]:
                    self.average_result[index] = value
                else:
                    self.average_result[index] += value

        # Calculating average.
        for index, value in enumerate(self.average_result):
            # If the result has not digital values, we should assign this values to the result variable without averaging
            if type(value) not in [int, float]:
                self.average_result[index] = value
            else:
                self.average_result[index] = round(value / len(self.data), 3)

    def is_better_point(self, is_minimization_experiment, solution_candidate):
        if is_minimization_experiment is True:
            if solution_candidate < self:
                return True
            else:
                return False
        elif is_minimization_experiment is False:
            if solution_candidate > self:
                return True
            else:
                return False

