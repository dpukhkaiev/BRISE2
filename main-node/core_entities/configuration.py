import logging
from functools import reduce
import numpy as np


class Configuration:

    def __init__(self, parameters):
        """
        :param parameters: list with parameters
               shape - list, e.g. ``[1200, 32]``


        During initializing following fields are declared:

        self.__parameters:              shape - list, e.g. ``[2900.0, 32]``
        self.__parameters_in_indexes:   shape - list, e.g. ``[1, 8]``
        self._tasks:                    shape - dict, e.g.
                                               ``{
                                                    id_task_1: {
                                                       "result": result1,
                                                       "worker": worker_name1
                                                    },
                                                    id_task_2: {
                                                      "result": result2,
                                                      "worker": worker_name2
                                                    },
                                                    ...
                                                 }``

                                         id_task:      shape - int or string
                                         result:       shape - list, e.g. ``[700.56]``
                                         worker_name:  shape - string

        self._average_result:            shape - list, e.g. ``[806.43]``
        self._predicted_result:          shape - list, e.g. ``[0.0098776]``
        """

        self.logger = logging.getLogger(__name__)

        if all(isinstance(value, (int, float, str)) for value in parameters):
            self.__parameters = parameters
        else:
            self.logger.error("Parameters %s are not int, float or str type" % parameters)

        self.__parameters_in_indexes = []
        self._tasks = {}
        self._average_result = []
        self.predicted_result = []

    def add_predicted_result(self, parameters, predicted_result):

        if self.__is_valid_configuration(parameters):
            self.predicted_result = predicted_result

    def add_tasks(self, parameters, task_id, result, worker):
        """
        Add new measurements of concrete parameters
        :param parameters: List with parameters. Used for validation
        :param task_id: Integer or String, Task identifier
        :param result: List of task results
        :param worker: String, Worker identifier
        """

        if self.__is_valid_configuration(parameters) and self.__is_valid_task(task_id, result, worker):
            if task_id and result and worker:
                self._tasks[task_id] = {
                    "result": result,
                    "worker": worker
                }
                self.__calculate_average_result()

    def add_parameters_in_indexes(self, parameters, parameters_in_indexes):
        if self.__is_valid_configuration(parameters):
            self.__parameters_in_indexes = parameters_in_indexes

    def get_parameters(self):
        return self.__parameters.copy()

    def get_parameters_in_indexes(self):
        return self.__parameters_in_indexes.copy()

    def get_tasks(self):
        return self._tasks.copy()

    def get_average_result(self):
        return self._average_result.copy()

    def is_better_configuration(self, is_minimization_experiment, current_best_solution):
        """
        Returns bool value. True - self is better then  current_best_solution, otherwise False.
        :param is_minimization_experiment: bool, is taken from json file description
        :param current_best_solution: configuration instance
        :return: bool
        """
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
        """
        Validate type of fields in configuration task
        :param task_id: number or string, task identifier
        :param result: list of task results
        :param worker: string, worker identifier
        :return: bool
        """
        if isinstance(result, list) and all(isinstance(value, (int, float)) for value in result) \
                and type(task_id) in [int, float, str] and worker is not "":
            return True
        else:
            if not isinstance(result, list):
                self.logger.error('Current result %s is not a list' % result)
            if not all(isinstance(value, (int, float)) for value in result):
                self.logger.error('Current results\' values %s are not int or float type' % result)
            if type(task_id) not in [int, float, str]:
                self.logger.error('Current task_id %s is not int or float or str type' % task_id)
            if worker is "":
                self.logger.error('Current worker is empty string') 
            return False
        
    def __is_valid_configuration(self, parameters):
        """
         Is parameters equal to instance parameters
        :param parameters: list
        :return: bool
        """
        if parameters == self.get_parameters():
            return True
        else:
            self.logger.error('New configuration %s does not match with current configuration %s'
                              % (parameters, self.get_parameters()))
            return False

    def __calculate_average_result(self):
        """
        Updates average result for valid configuration tasks.
        Takes the list of results from each task, it is considered there are no numerical values.
        Calculates an average result from the final list.
        """
        # list of a result list from all tasks
        results_tuples = [task["result"] for (_, task) in self._tasks.items()]
        # calculating the average over all result items
        self._average_result = np.mean(results_tuples, axis=0).tolist()
