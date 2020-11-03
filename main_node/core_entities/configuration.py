from __future__ import annotations

import json
import logging
import pickle
import uuid
from collections import OrderedDict
from copy import deepcopy
from enum import Enum
from typing import Any, Dict, List, Mapping, MutableMapping, Tuple

import pandas as pd
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

    def __init__(self, parameters: Mapping, config_type: Type, experiment_id: str):
        """
        :param hyperparameters: hyperparameters mapping name:value
               shape - ``{"Frequency": 1200, "Threads": 32}``
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
        self._parameters: MutableMapping = OrderedDict()
        self.parameters = parameters
        self._tasks = {}
        self._results: Mapping = OrderedDict()
        self.predicted_result = []
        self.type = config_type
        self.status = Configuration.Status.NEW
        # Meta information
        self._standard_deviation = []
        self.is_enabled = True
        self.number_of_failed_tasks = 0
        self._task_number = 0
        self.warm_startup_info = {}
        self.experiment_id = experiment_id

    def __getstate__(self) -> Dict[str, Any]:
        space = self.__dict__.copy()
        space['status'] = int(space['status'])
        space['type'] = int(space['type'])
        space["_parameters"] = dict(space["_parameters"])
        space["_results"] = dict(space["_results"])
        del space['logger']
        return deepcopy(space)

    def __setstate__(self, space: Dict[str, Any]) -> None:
        self.__dict__ = space
        self.logger = logging.getLogger(__name__)
        self.status = Configuration.Status(space['status'])
        self.type = Configuration.Type(space['type'])
        self._parameters = OrderedDict(space["_parameters"])
        self._results = OrderedDict(space["_results"])

    @property
    def parameters(self) -> MutableMapping:
        return deepcopy(self._parameters)

    @parameters.setter
    def parameters(self, parameters: MutableMapping):
        if not isinstance(parameters, Mapping):
            raise TypeError(f"Parameters should be of instance {type(self._parameters)}.")
        elif not all((self._parameters[h] == parameters[h] for h in self._parameters)):
            raise ValueError(f"Previously selected parameters should not be altered! "
                             f"{self._parameters} != {parameters}")
        if parameters.get("low level heuristic", "") == "jMetalPy.EvolutionStrategy":
            if 'lambda_' in parameters and parameters['lambda_'] < parameters['mu']:
                self.logger.warning(f"Values for 'lambda_'({parameters['lambda_']}( and 'mu'({parameters['mu']}) "
                                    f"parameters was swapped due to specifics of MH!")
                parameters['lambda_'], parameters['mu'] = parameters['mu'], parameters['lambda_']
        self._parameters = parameters

    @property
    def results(self) -> Mapping:
        return deepcopy(self._results)

    @results.setter
    def results(self, results: Mapping):
        if not isinstance(results, Mapping):
            raise TypeError(f"Results should be of instance {type(self._results)}.")
        else:
            self._results = OrderedDict(results)

    def to_series(self, results: bool = True) -> pd.Series:
        data = OrderedDict(self.parameters)
        if results:
            data.update(self.results)
        return pd.Series(data, dtype='object')

    def add_predicted_result(self, *args, **kwargs) -> None:
        # the structure of predicted results should be revised to:
        # 1. support tree-shaped search space
        # 2. reflect the meaning of each model's prediction sense (regression surrogate prediction is real value, while
        # TPE prediction is probability
        raise NotImplementedError

    def add_task(self, task: Mapping) -> None:
        """
        Add new measurements of concrete parameters
        :param task: mapping of task results
        """
        task_id = task["task id"]
        self.warm_startup_info = task["result"].pop("warm_startup_info", {})
        self._tasks[str(task_id)] = task
        self._assemble_tasks_results()

    def get_tasks(self) -> Mapping:
        return self._tasks.copy()

    def get_required_results_with_marks_from_all_tasks(self) -> Tuple[List[OrderedDict], List[str]]:
        from_all_tasks = []
        marks = []
        for task in self._tasks.values():
            from_one_task = OrderedDict()
            for domain in self.__class__.TaskConfiguration["Objectives"]:
                from_one_task[domain] = (task['result'][domain])
            from_all_tasks.append(from_one_task)
            marks.append(task['ResultValidityCheckMark'])
        return from_all_tasks, marks

    def get_standard_deviation(self):
        return self._standard_deviation.copy()

    def to_json(self) -> str:
        dictionary_dump = {"configuration_id": self.unique_id,
                           "parameters": self.parameters,
                           "results": self.results,
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
    def from_json(json_string: str) -> Configuration:
        dictionary_dump: dict = json.loads(json_string)
        conf = Configuration(dictionary_dump["parameters"], dictionary_dump["type"], dictionary_dump["experiment_id"])
        conf.results = dictionary_dump["results"]
        conf.unique_id = dictionary_dump["configuration_id"]
        conf._tasks = dictionary_dump["tasks"]
        conf.predicted_result = dictionary_dump["predicted_result"]
        conf._standard_deviation = dictionary_dump["standard_deviation"]
        conf.type = Configuration.Type(dictionary_dump["type"])
        conf.status = Configuration.Status(dictionary_dump["status"])
        conf.is_enabled = dictionary_dump["is_enabled"]
        conf.number_of_failed_tasks = dictionary_dump["number_of_failed_tasks"]
        conf._task_number = dictionary_dump["_task_number"]
        conf.warm_startup_info = dictionary_dump["warm_startup_info"]
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
        if self.results and other.results:
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

    def __eq__(self, other: Configuration) -> bool:
        if not isinstance(other, Configuration):
            return False
        return self.unique_id == other.unique_id or self.parameters == other.parameters

    def __lt__(self, other: Configuration) -> bool:
        """
        Returns True, if 'self' < 'compared_configuration'. Otherwise - False
        :param other: instance of Configuration class
        :return: bool
        """
        objectives = self.__class__.TaskConfiguration["Objectives"]
        assert all((objective in self.results.keys() for objective in objectives)), f"{self} does not contain all {objectives}."
        assert all((objective in other.results.keys() for objective in objectives)), f"{other} does not contain all {objectives}."
        assert self.results.keys() == other.results.keys(), f"Unable to compare Configurations since objectives do not match: {self}, {other}"

        # compare all metrics
        objectives_comparison = dict()
        for objective, result in self.results.items():
            objectives_comparison[objective] = result < other.results[objective]

        priorities = self.__class__.TaskConfiguration["ObjectivesPriorities"]
        # get highest priority objectives
        highest_priority_indexes = [index for index, priority in enumerate(priorities) if priority == max(priorities)]
        influencing_objectives = [objectives[index] for index in highest_priority_indexes]

        # get all comparisons for the highest priority
        resulting_comparisons = dict((objctv, objectives_comparison[objctv]) for objctv in influencing_objectives)

        # all comparisons are True for the same priority == dominating solution
        if all(obj_comp is True for obj_comp in resulting_comparisons.values()):
            return True
        elif all(obj_comp is False for obj_comp in resulting_comparisons.values()):
            return False
        else:
            self.logger.warning(f"Got non-dominating Configuration comparison: "
                                f"{self} VS {other} -> {resulting_comparisons}")
            return False

    def __gt__(self, other: Configuration) -> bool:
        """
        Returns True, if 'self' > 'compared_configuration'. Otherwise - False
        :param other: instance of Configuration class
        :return: bool
        """
        return other.__lt__(self)

    def _assemble_tasks_results(self) -> None:
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
        ok_tasks_results = pd.DataFrame(results_tuples, columns=self.TaskConfiguration["Objectives"])
        self.results = OrderedDict(ok_tasks_results.mean())
        self._standard_deviation = ok_tasks_results.std().to_list()
        self._task_number = len(results_tuples)

    def __repr__(self) -> str:
        """
        String representation of Configuration object.
        """
        return f"Configuration(" \
               f"Params={str(dict(self.parameters))}, " \
               f"Tasks={len(self._tasks)}, " \
               f"Outliers={len(self._tasks) - self._task_number}, " \
               f"Avg.result={str(dict(self.results))}, " \
               f"STD={str(self.get_standard_deviation())}" \
               ")"

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

    def get_configuration_record(self) -> Mapping:
        '''
        The helper method that formats a configuration to be stored as a record in a Database
        :return: Mapping. Field names of the database collection with respective information
        '''
        record = {}
        record["Exp_unique_ID"] = self.experiment_id
        record["Configuration_ID"] = self.unique_id
        record["Parameters"] = self.parameters
        record["Type"] = self.type
        record["Status"] = self.status
        record["Results"] = self.results
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
