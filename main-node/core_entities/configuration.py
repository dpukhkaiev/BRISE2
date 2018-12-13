import logging


class Configuration:

    def __init__(self, parameters):
        """
        :param parameters: list with parameters
               shape - list, e.g. ``[1200, 32]``


        During initializing following fields are declared:

        self.parameters:             shape - list, e.g. ``[2900.0, 32]``
        self.parameters_in_indexes:  shape - list, e.g. ``[1, 8]``
        self._tasks:                    shape - dict, e.g.
                                               ``{
                                                    id_task_1: {
                                                       "result": result1,
                                                       "worker": worker_name1
                                                    }
                                                    id_task_2: {
                                                      "result": result2,
                                                      "worker": worker_name2
                                                    }
                                                    ...
                                                 }``
                                        id_task_1:    shape - int or string
                                        result:       shape - list, e.g. ``[700.56]``
                                        worker_name:  shape - string

        self._average_result:            shape - list, e.g. ``[806.43]``
        self._predicted_result:          shape - list, e.g. ``[0.0098776]``
        """

        self.logger = logging.getLogger(__name__)

        self.parameters = parameters
        self.parameters_in_indexes = []
        self._tasks = {}
        self._average_result = []
        self.predicted_result = []

    def add_predicted_result(self, parameters, predicted_result):

        if self.__is_valid_configuration(parameters):
            self.predicted_result = predicted_result

    def add_tasks(self, parameters, task_id, result, worker):

        if self.__is_valid_configuration(parameters) and self.__is_valid_task(task_id, result, worker):
            if task_id and result and worker:
                self._tasks[task_id] = {
                    "result": result,
                    "worker": worker
                }
                self.__calculate_average_result()

    def get_tasks(self):
        return self._tasks.copy()

    def get_average_result(self):
        return self._average_result.copy()

    def is_better_configuration(self, is_minimization_experiment, current_best_solution):
        if self.get_average_result() != [] and current_best_solution.get_average_result() != []:
            if is_minimization_experiment is True:
                if self < current_best_solution:
                    return True
                else:
                    return False
            elif is_minimization_experiment is False:
                if self > current_best_solution:
                    return True
                else:
                    return False
        elif self.get_average_result() == [] or current_best_solution.get_average_result() == []:
            self.logger.error('On of the object has empty average_result: self.average_result = %s, \
                               solution_candidate.get_average_result = %s'
                              % (self.get_average_result(), current_best_solution.get_average_result()))

    def __lt__(self, compared_configuration):
        """
        Returns True, if 'self' < 'compared_configuration'. Otherwise - False
        :param compared_configuration: instance of Configuration class
        :return: True or False
        """
        return self.get_average_result()[0] < compared_configuration.get_average_result()[0]

    def __gt__(self, compared_configuration):
        """
        Returns True, if 'self' > 'compared_configuration'. Otherwise - False
        :param compared_configuration: instance of Configuration class
        :return: True or False
        """
        return compared_configuration.__lt__(self)

    def __is_valid_task(self, task_id, result, worker):
        if isinstance(result, list) and type(task_id) in [int, float, str] and worker is not "":
            return True

        if not isinstance(result, list):
            self.logger.error('Current result %s is a list' % result)
        if type(task_id) not in [int, float, str]:
            self.logger.error('Current task_id %s is not int or float or str type' % task_id)
        if worker is "":
            self.logger.error('Current worker is empty string')
        return False

    def __is_valid_configuration(self, parameters):
        if parameters == self.parameters:
            return True
        else:
            self.logger.error('New configuration %s does not match with current configuration %s'
                              % (parameters, self.parameters))
            return False

    def __calculate_average_result(self):
        """
         Calculating average result for configuration
        """
        # create a list
        average_result_length = 0
        for sub_dictionary_key, sub_dictionary in self.get_tasks().items():
            average_result_length = len(sub_dictionary["result"])
            break
        self._average_result = [0 for x in range(average_result_length)]

        for key, key_dict in self.get_tasks().items():
            for index, value in enumerate(key_dict["result"]):
                # If the result doesn't have digital values, these values should be assigned  to the result variable
                # without averaging
                if type(value) not in [int, float]:
                    self._average_result[index] = value
                else:
                    self._average_result[index] += value

        # Calculating average.
        for index, value in enumerate(self._average_result):
            # If the result has not digital values, we should assign this values to the result variable without averaging
            if type(value) not in [int, float]:
                self._average_result[index] = value
            else:
                self._average_result[index] = value / len(self.get_tasks())
