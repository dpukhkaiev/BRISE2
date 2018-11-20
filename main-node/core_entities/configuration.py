import logging


class Configuration:
    # The shape of configuration - list, e.g.
    #                              [2900.0, 32]
    configuration = []

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
    data = {}

    # The shape of average_result - list with one average value of 'result' fields in 'data', e.g.
    #                               [806.43]
    average_result = []

    def __init__(self, configuration, task_id, result, worker):
        self.logger = logging.getLogger(__name__)
        self.configuration = configuration
        self.data[task_id] = {
            "result": result,
            "worker": worker
        }
        self.calculate_average_result()

    def add_data(self, configuration, task_id, result, worker):

        if self.configuration == []:
            self.configuration = configuration

        if self.configuration == configuration:
            self.data[task_id] = {
                "result": result,
                "worker": worker
            }
            self.calculate_average_result()
        else:
            self.logger.error('New configuration %s does not match with current configuration %s'
                              % (configuration, self.configuration), exc_info=True)

    def __lt__(self, compared_configuration):
        """
        Returns True, if 'self' < 'compared_configuration'. Otherwise - False
        :param compared_configuration: instance of Configuration class
        :return: True or False
        """
        return self.average_result < compared_configuration.average_result

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
        self.average_result = [0 for x in range(len(self.data[0]["result"]))]
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
