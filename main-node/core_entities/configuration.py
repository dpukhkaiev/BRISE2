from __future__ import annotations
import json
import logging
import uuid
import pickle
from enum import Enum
from copy import deepcopy
from typing import Iterable, Mapping, List

import numpy as np

from tools.front_API import API


class Configuration:
    class Type(int, Enum):
        DEFAULT = 0
        PREDICTED = 1
        FROM_SELECTOR = 2
        TEST = 3

    class Status(int, Enum):
        NEW = 0
        EVALUATED = 1
        REPEATED_MEASURING = 2
        MEASURED = 3
        BAD = 4

    TaskConfiguration = {}

    @classmethod
    def set_task_config(cls, taskConfig):
        cls.TaskConfiguration = taskConfig

    def __init__(self, parameters: Iterable, config_type: Type):
        """
        :param parameters: Iterable object.
            While iterating, should return parameter values in the same order as in HyperparameterNames of
            Experiment Description. During initialization it will be converted into the tuple.
            Example: list, e.g. ``[1200, 32]`` will be converted to (1200, 32),
        :param config_type: Configuration Type (see inner class Type).

        During initializing following fields are declared:

        self.parameters:               shape - tuple, e.g. ``(2900.0, 32)``. One-time-set property.
        self._parameters_in_indexes:   shape - list, e.g. ``[1, 8]``
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
        self.type:                      shape - Configuration.Type, e.g   ``DEFAULT``
        """
        self.logger = logging.getLogger(__name__)
        # The unique configuration ID
        self.unique_id = str(uuid.uuid4())
        self._parameters = parameters
        self._parameters_in_indexes = []
        self._tasks = {}
        self._average_result = []
        self.predicted_result = []
        self.type = config_type
        self.status = Configuration.Status.NEW
        # Meta information
        self._standard_deviation = []
        self.is_enabled = True
        self.number_of_failed_tasks = 0
        self._task_number = 0
        self.warm_startup_info = {}
        self.experiment_id = None

    def __getstate__(self):
        space = self.__dict__.copy()
        space['status'] = int(space['status'])
        space['type'] = int(space['type'])
        del space['logger']
        return deepcopy(space)

    def __setstate__(self, space):
        self.__dict__ = space
        self.logger = logging.getLogger(__name__)
        self.status = Configuration.Status(space['status'])
        self.type = Configuration.Type(space['type'])

    def __eq__(self, other):
        if not isinstance(other, Configuration):
            return False
        # TODO: This is a temporal solution. More details at:
        #  https://github.com/dpukhkaiev/BRISEv2/pull/145#discussion_r446104461
        return self.unique_id == other.unique_id or self.parameters == other.parameters

    def _set_parameters(self, parameters):
        if not self._parameters:
            self._parameters = tuple(parameters)
        else:
            self.logger.error("Unable to update Experiment Description: Read-only property.")
            raise AttributeError("Unable to update Experiment Description: Read-only property.")

    def _get_parameters(self):
        return deepcopy(self._parameters)

    def _del_parameters(self):
        if self._parameters:
            self.logger.error("Unable to delete Experiment Description: Read-only property.")
            raise AttributeError("Unable to update Experiment Description: Read-only property.")

    parameters = property(_get_parameters, _set_parameters, _del_parameters)

    def add_predicted_result(self, parameters: list, predicted_result: list):

        if self.__is_valid_configuration(parameters):
            self.predicted_result = [float(x) for x in predicted_result]

    def add_tasks(self, task):
        """
        Add new measurements of concrete parameters
        :param task: List of task results
        """
        task_id = task["task id"]
        self.warm_startup_info = task["result"].pop("warm_startup_info", {})
        self._tasks[str(task_id)] = task
        self.__assemble_tasks_results()

    def add_parameters_in_indexes(self, parameters, parameters_in_indexes):
        if self.__is_valid_configuration(parameters):
            self._parameters_in_indexes = parameters_in_indexes

    def get_parameters_in_indexes(self):
        return self._parameters_in_indexes.copy()

    def get_tasks(self):
        return self._tasks.copy()

    def get_average_result(self):
        return self._average_result.copy()

    def get_required_results_with_marks_from_all_tasks(self):
        from_all_tasks = []
        marks = []
        for task in self._tasks.values():
            from_one_task = []
            for domain in self.__class__.TaskConfiguration["Objectives"]:
                from_one_task.append(task['result'][domain])
            from_all_tasks.append(from_one_task)
            marks.append(task['ResultValidityCheckMark'])
        return from_all_tasks, marks

    def get_standard_deviation(self):
        return self._standard_deviation.copy()

    def to_json(self):
        # TODO: this method partially repeats the functionality of 'Configuration.get_configuration_record()'. Refactoring needed 
        dictionary_dump = {"configuration_id": self.unique_id,
                           "parameters": self._parameters,
                           "parameters_in_indexes": self._parameters_in_indexes,
                           "average_result": self._average_result,
                           "tasks": self._tasks,
                           "predicted_result": self.predicted_result,
                           "standard_deviation": self._standard_deviation,
                           "type": self.type,
                           "status": self.status,
                           "is_enabled": self.is_enabled,
                           "number_of_failed_tasks": self.number_of_failed_tasks,
                           "_task_number": self._task_number,
                           "warm_startup_info": self.warm_startup_info,
                           "experiment_id": self.experiment_id
                           }
        return json.dumps(dictionary_dump)

    @staticmethod
    def from_json(json_string):
        # TODO: communication should be reworked in a way that we avoid using this method 
        # (as it creates additional physical objects for a single logical configuration)
        dictionary_dump = json.loads(json_string)
        conf = Configuration(dictionary_dump["parameters"], dictionary_dump["type"])
        # Configuration id is rewritten here, which is undesirable behavior
        conf.unique_id = dictionary_dump["configuration_id"]
        conf._parameters_in_indexes = dictionary_dump["parameters_in_indexes"]
        conf._average_result = dictionary_dump["average_result"]
        conf._tasks = dictionary_dump["tasks"]
        conf.predicted_result = dictionary_dump["predicted_result"]
        conf._standard_deviation = dictionary_dump["standard_deviation"]
        conf.type = Configuration.Type(dictionary_dump["type"])
        conf.status = Configuration.Status(dictionary_dump["status"])
        conf.is_enabled = dictionary_dump["is_enabled"]
        conf.number_of_failed_tasks = dictionary_dump["number_of_failed_tasks"]
        conf._task_number = dictionary_dump["_task_number"]
        conf.warm_startup_info = dictionary_dump["warm_startup_info"]
        conf.experiment_id = dictionary_dump["experiment_id"]
        return conf

    def is_better(self, o_minimize: List[bool], o_prio: List[int], other: Configuration) -> bool:
        """
        Comparison of Configurations on their Objective values.

        :param o_minimize: list of boolean values. Indicates the direction of optimization for each objective.
        :param o_prio: list of integers. Indicates the priorities among objectives for comparison.
        :param other: configuration instance, against which the comparison is performed.
        :return: bool True - this configuration is better then 'other', otherwise False.
        """
        top_prio_index = o_prio.index(max(o_prio))
        if self.get_average_result() != [] and other.get_average_result() != []:
            if o_minimize[top_prio_index] is True:
                if self < other:
                    return True
                else:
                    return False
            elif o_minimize[top_prio_index] is False:
                if self > other:
                    return True
                else:
                    return False
        else:
            self.logger.error(f"One (or both) of Configurations doesn't (don't) have the results: {self}, {other}.")

    def __lt__(self, other: Configuration) -> bool:
        """
        Returns True, if 'self' < 'compared_configuration'. Otherwise - False
        :param other: instance of Configuration class
        :return: bool
        """
        # compare all metrics
        dimension_wise_comparison = []
        for i in range(len(self.get_average_result())):
            dimension_wise_comparison.append(
                self.get_average_result()[i] < other.get_average_result()[i])

        priorities = self.__class__.TaskConfiguration["ObjectivesPriorities"]
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

    def __gt__(self, other: Configuration):
        """
        Returns True, if 'self' > 'compared_configuration'. Otherwise - False
        :param other: instance of Configuration class
        :return: bool
        """
        return other.__lt__(self)

    def __is_valid_configuration(self, parameters):
        """
         Is parameters equal to instance parameters
        :param parameters: list
        :return: bool
        """
        if parameters == self.parameters:
            return True
        else:
            self.logger.error('New configuration %s does not match with current configuration %s'
                              % (parameters, self.parameters))
            return False

    def __assemble_tasks_results(self):
        """
        Updates the results of the Configuration measurement by aggregating the results from all available Tasks.
        The Average Results of the Configuration and the Standard Deviation between Tasks are calculated.
        """
        # list of a result list from all tasks
        results_tuples, marks = self.get_required_results_with_marks_from_all_tasks()
        task_index_size = len(results_tuples) - 1
        # delete marked bad/outliers values before average is calculated
        for task_index in range(task_index_size, -1, -1):
            if marks[task_index] == 'Bad value' or \
                    marks[task_index] == 'Outlier' or \
                    marks[task_index] == 'Out of bounds':
                del(results_tuples[task_index])
        # calculating the average over all result items
        self._average_result = np.mean(results_tuples, axis=0).tolist()
        self._standard_deviation = np.std(results_tuples, axis=0).tolist()
        self._task_number = len(results_tuples)

    def __repr__(self):
        """
        String representation of Configuration object.
        """
        return "Configuration(Params={params}, Tasks={num_of_tasks}, Outliers={num_of_outliers}, " \
               "Avg.result={avg_res}, STD={std})".format(
            params=str(self.parameters),
            num_of_tasks=len(self._tasks),
            num_of_outliers=len(self._tasks) - self._task_number,
            avg_res=str(self.get_average_result()),
            std=str(self.get_standard_deviation()))

    def disable_configuration(self):
        """
        Disable configuration. This configuration won't be used in experiment.
        """
        if self.is_enabled:
            self.is_enabled = False
            temp_msg = f"Configuration {self} was disabled. It will not be added to the Experiment."
            self.logger.warning(temp_msg)
            API().send('log', 'warning', message=temp_msg)

    def increase_failed_tasks_number(self):
        """
        Increase counter of failed measures.
        """
        self.number_of_failed_tasks = self.number_of_failed_tasks + 1

    def is_valid_task(self, task: dict):
        """
        Check error_check function output and return an appropriate flag
        :param task: dictionary object, that represents one Task
        :return: boolean, should we include task to configuration or not
        """
        try:
            assert isinstance(task, dict), "Task is not a dictionary object."
            if task["ResultValidityCheckMark"] == "Bad value" or task["ResultValidityCheckMark"] == "Out of bounds":
                return False
            assert type(task["task id"]) in [int, float, str], "Task IDs are not hashable: %s" % type(task["task id"])
            assert task['worker'], "Worker is not specified: %s" % task
            assert set(self.TaskConfiguration['Objectives']) <= set(task['result'].keys()), \
                f"All required result fields are not obtained. " \
                f"Expected: {self.TaskConfiguration['Objectives']}. Got: {task['result'].keys()}."
            return True
        except AssertionError as error:
            logging.getLogger(__name__).error("Unable to add Task (%s) to Configuration. Reason: %s" % (task, error))
            return False

    def get_configuration_record(self, experiment_id: str) -> Mapping:
        '''
        The helper method that formats a configuration to be stored as a record in a Database
        :return: Mapping. Field names of the database collection with respective information
        '''
        record = {}
        record["Exp_unique_ID"] = experiment_id
        record["Configuration_ID"] = self.unique_id
        record["Parameters"] = self.parameters
        record["Type"] = self.type
        record["Status"] = self.status
        record["Parameters_in_indexes"] = self._parameters_in_indexes
        record["Average_result"] = self._average_result
        record["Predicted_result"] = self.predicted_result
        record["Standard_deviation"] = self._standard_deviation
        record["is_enabled"] = self.is_enabled
        record["Number_of_failed_tasks"] = self.number_of_failed_tasks
        record["ConfigurationObject"] = pickle.dumps(self)
        return record

    def get_task_record(self, task: dict) -> Mapping:
        '''
        The helper method that formats a task description to be stored as a record in a Database
        :return: Mapping. Field names of the database collection with respective information
        '''
        record = {}
        record["Configuration_ID"] = self.unique_id
        record["Task_ID"] = task['task id']
        record["Task"] = task
        return record
