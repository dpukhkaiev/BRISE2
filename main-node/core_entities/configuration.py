import logging
import numpy as np


class Configuration:

    TaskConfiguration = {}
    @classmethod
    def set_task_config(cls, tasrConfig):
        cls.TaskConfiguration = tasrConfig

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
            raise TypeError("Wrong parameter types for initialization new Configuration. Supported numeric or string.")

        self.__parameters_in_indexes = []
        self._tasks = {}
        self._average_result = []
        self.predicted_result = []
        # Meta information
        self._standard_deviation = []

    def __getstate__(self):
        space = self.__dict__.copy()
        del space['logger']
        return space

    def __setstate__(self, space):
        self.__dict__ = space
        self.logger = logging.getLogger(__name__)

    def add_predicted_result(self, parameters: list, predicted_result: list):

        if self.__is_valid_configuration(parameters):
            self.predicted_result = [float(x) for x in predicted_result]

    def add_tasks(self, parameters, task):
        """
        Add new measurements of concrete parameters
        :param parameters: List with parameters. Used for validation
        :param task: List of task results
        """

        if self.__is_valid_configuration(parameters) and self.__is_valid_task(task):
            task_id = task["task id"]
            self._tasks[str(task_id)] = task
            self.__assemble_tasks_results()

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

    def get_required_results_from_all_tasks(self):
        from_all_tasks = []
        for task in self._tasks.values():
            from_one_task = []
            for domain in self.__class__.TaskConfiguration["ResultStructure"]:
                from_one_task.append(task['result'][domain])
            from_all_tasks.append(from_one_task)
        return from_all_tasks

    def get_standard_deviation(self):
        return self._standard_deviation.copy()

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
        :return: bool
        """
        # compare all metrics
        dimension_wise_comparison = []
        for i in range(len(self.get_average_result())):
            dimension_wise_comparison.append(self.get_average_result()[i] < compared_configuration.get_average_result()[i])

        # get priorities or use the same values if unspecified
        priorities = self.__class__.TaskConfiguration["ResultPriorities"] \
            if "ResultPriorities" in self.__class__.TaskConfiguration else [0] * len(dimension_wise_comparison)

        # filter highest priorities
        highest_priority_indexes = [index for index, priority in enumerate(priorities) if priority == max(priorities)]

        # get all comparisons for the highest priority
        dimensions_with_highest_priorities = []
        for i in highest_priority_indexes:
            dimensions_with_highest_priorities.append(dimension_wise_comparison[i])

        # all comparisons are equal for the same priority == dominating solution
        if all(elem == dimensions_with_highest_priorities[0] for elem in dimensions_with_highest_priorities):
            return dimensions_with_highest_priorities[0]
        else:
            return False

    def __gt__(self, compared_configuration):
        """
        Returns True, if 'self' > 'compared_configuration'. Otherwise - False
        :param compared_configuration: instance of Configuration class
        :return: bool
        """
        return compared_configuration.__lt__(self)

    @classmethod
    def __is_valid_task(cls, task):
        """
        Validate type of fields in configuration task
        :param task: list of task results
        :return: bool
        """

        try:
            assert isinstance(task, dict), "Task is not a dictionary object."
            assert type(task["task id"]) in [int, float, str], "Task IDs are not hashable: %s" % type(task["task id"])
            assert task['worker'], "Worker is not specified: %s" % task
            # assuming, we have a 'TaskConfiguration' field of Experiment description stored in Configuration (could be as static field)
            assert set(cls.TaskConfiguration['ResultStructure']) <= set(task['result'].keys()), \
                "All required result fields are not obtained. Expected: %s. Got: %s." % (
                cls.TaskConfiguration["ResultStructure"], task['result'].keys())
            for dim_name, dim_data_type in zip(cls.TaskConfiguration["ResultStructure"], cls.TaskConfiguration["ResultDataTypes"]):
                assert type(task['result'][dim_name]).__name__ == dim_data_type, \
                "Result types are not match Experiment Description: %s. Expected: %s." % (str([str(type(x)) for x in task['result']]), cls.TaskConfiguration["ResultDataTypes"])
            return True
        except AssertionError as error:
            logging.getLogger(__name__).error("Unable to add Task (%s) to Configuration. Reason: %s" % (task, error))
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

    def __assemble_tasks_results(self):
        """
        Updates the results of the Configuration measurement by aggregating the results from all available Tasks.
        The Average Results of the Configuration and the Standard Deviation between Tasks are calculated.
        """
        results_tuples = self.get_required_results_from_all_tasks()
        # calculating the average over all result items
        self._average_result = np.mean(results_tuples, axis=0).tolist()
        self._standard_deviation = np.std(results_tuples, axis=0).tolist()

    def __repr__(self):
        """
        String representation of Configuration object.
        """
        return "Configuration(Params={params}, Tasks={num_of_tasks}, Avg.result={avg_res}, STD={std})".format(
            params=str(self.get_parameters()),
            num_of_tasks=len(self._tasks),
            avg_res=str(self.get_average_result()),
            std=str(self.get_standard_deviation()))
