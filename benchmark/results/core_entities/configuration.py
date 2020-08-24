from __future__ import annotations
import logging
import json
from enum import Enum
from typing import Mapping, Any, Dict
from copy import deepcopy
from collections import OrderedDict

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

    def __init__(self, hyperparameters: Mapping, config_type: Type):
        """
        :param hyperparameters: hyperparameters mapping name:value
               shape - ``{"Frequency": 1200, "Threads": 32}``
        :param config_type: Configuration Type (see inner class Type).
        """
        self.logger = logging.getLogger(__name__)
        self._hyperparameters = OrderedDict()
        self._parameters = hyperparameters
        self.hyperparameters = hyperparameters
        self._average_result = []
        self._results: OrderedDict = OrderedDict()
        self._tasks = {}
        self.type = config_type
        self.status = Configuration.Status.NEW
        # Meta information
        self.predicted_result = []
        self._standard_deviation = []
        self.is_enabled = True
        self.number_of_failed_tasks = 0
        self._task_amount = 0
        self.warm_startup_info = {}   # is getting from the last added Task, could be refactored later

    @property
    def hyperparameters(self):
        # TODO: replace deepcopy with immutable mappings.
        if "_hyperparameters" in dir(self):
            # we are working with 'new' configuration
            return deepcopy(self._hyperparameters)
        else:
            # we are working with "old" configuration, its an ad-hoc trick for benchmarks..
            p_names = ["low level heuristic"]
            for i in range(len(self._parameters) - 1):
                p_names.append(str(i))
            return dict(zip(p_names, self._parameters))

    @hyperparameters.setter
    def hyperparameters(self, hyperparameters: OrderedDict):
        if not isinstance(hyperparameters, Mapping):
            raise TypeError(f"Hyperparameters should be of instance {type(self._hyperparameters)}")
        elif not all((self._hyperparameters[h] == hyperparameters[h] for h in self._hyperparameters)):
            raise ValueError(f"Previously selected hyperparameters should not be altered! "
                             f"{self._hyperparameters} != {hyperparameters}")
            # check that Hyperparameters were not altered:
        else:
            # --- TODO: work-around, should be removed
            if hyperparameters.get("low level heuristic", "") == "jMetalPy.EvolutionStrategy":
                if 'lambda_' in hyperparameters:
                    if hyperparameters['lambda_'] < hyperparameters['mu']:
                        self.logger.warning(f"Hyperparameter 'lambda_' was altered from {hyperparameters['lambda_']} to"
                                            f" {hyperparameters['mu']}!")
                        hyperparameters['lambda_'] = hyperparameters['mu']
            # --- end work-around
            self._hyperparameters = OrderedDict(hyperparameters)

    @property
    def results(self):
        if "_hyperparameters" in dir(self):
            # we are working with 'new' configuration
            return deepcopy(self._results)
        else:
            # we are working with "old" configuration
            return dict(zip(self.__class__.TaskConfiguration["ResultStructure"], self._average_result))

    @results.setter
    def results(self, results: OrderedDict):
        if not isinstance(results, Mapping):
            raise TypeError(f"Results should be of instance {type(self._results)}.")
        else:
            self._results = OrderedDict(results)

    def to_series(self, results: bool = True) -> pd.Series:
        data = self.hyperparameters
        if results:
            data.update(self.results)
        return pd.Series(data, dtype='object')

    def add_predicted_result(self, hyperparameters: list, predicted_result: list):
        if self._is_valid_configuration(hyperparameters):
            self.predicted_result = [float(x) for x in predicted_result]

    def add_task(self, task: Mapping) -> None:
        """
        Add new measurements of concrete parameters
        :param task: task results
        """
        task_id = task["task id"]
        self.warm_startup_info = task["result"].pop("warm_startup_info", {})
        self._tasks[str(task_id)] = task
        self._assemble_tasks_results()

    def get_tasks(self):
        return self._tasks.copy()

    def get_required_results_with_marks_from_all_tasks(self):
        from_all_tasks = []
        marks = []
        for task in self._tasks.values():
            from_one_task = OrderedDict()
            for domain in self.__class__.TaskConfiguration["ResultStructure"]:
                from_one_task[domain] = (task['result'][domain])
            from_all_tasks.append(from_one_task)
            marks.append(task['ResultValidityCheckMark'])
        return from_all_tasks, marks

    def get_standard_deviation(self):
        return self._standard_deviation.copy()

    # Serialization methods.
    # json:
    def to_json(self) -> str:
        dictionary_dump = {"hyperparameters": self.hyperparameters,
                           "results": self.results,
                           "predicted_result": self.predicted_result,
                           "standard_deviation": self._standard_deviation,
                           "type": self.type,
                           "status": self.status,
                           "is_enabled": self.is_enabled,
                           "tasks": self._tasks,
                           "number_of_failed_tasks": self.number_of_failed_tasks,
                           "_task_amount": self._task_amount,
                           "warm_startup_info": self.warm_startup_info
                           }
        return json.dumps(dictionary_dump)

    @staticmethod
    def from_json(json_string: str) -> Configuration:
        dictionary_dump: dict = json.loads(json_string)
        conf = Configuration(dictionary_dump["hyperparameters"], dictionary_dump["type"])
        conf.results = dictionary_dump["results"]
        conf.predicted_result = dictionary_dump["predicted_result"]
        conf._standard_deviation = dictionary_dump["standard_deviation"]
        conf.type = Configuration.Type(dictionary_dump["type"])
        conf.status = Configuration.Status(dictionary_dump["status"])
        conf.is_enabled = dictionary_dump["is_enabled"]
        conf._tasks = dictionary_dump["tasks"]
        conf.number_of_failed_tasks = dictionary_dump["number_of_failed_tasks"]
        conf._task_amount = dictionary_dump["_task_amount"]
        conf.warm_startup_info = dictionary_dump["warm_startup_info"]
        return conf

    # pickle:
    def __getstate__(self) -> Mapping:
        space = self.__dict__.copy()
        space['status'] = int(space['status'])
        space['type'] = int(space['type'])
        del space['logger']
        return deepcopy(space)

    def __setstate__(self, space: Dict[str, Any]) -> None:
        self.__dict__ = space
        self.logger = logging.getLogger(__name__)
        self.status = Configuration.Status(space['status'])
        self.type = Configuration.Type(space['type'])

    def is_better_configuration(self, is_minimization_experiment: bool, other: Configuration) -> bool:
        """
        Returns bool value. True - self is better then  current_best_solution, otherwise False.
        :param is_minimization_experiment: bool, is taken from json file description
        :param other: configuration instance
        :return: bool
        """
        if self.results and other.results:
            if is_minimization_experiment is True:
                if self < other:
                    return True
                else:
                    return False
            elif is_minimization_experiment is False:
                if self > other:
                    return True
                else:
                    return False
        elif not self.results or not other.results:
            raise ValueError(f"Could not compare Configurations because of empty results {self}, {other}.")

    def __eq__(self, other: Configuration):
        if not isinstance(other, Configuration):
            return False
        return self.hyperparameters == other.hyperparameters

    def __lt__(self, other: Configuration) -> bool:
        """
        Returns True, if 'self' < 'compared_configuration'. Otherwise - False
        :param other: instance of Configuration class
        :return: bool
        """
        if not isinstance(other, Configuration):
            raise TypeError(f"Could compare only {Configuration}, got {type(other)}.")
        # compare all metrics
        dimension_wise_comparison = []
        for key in self.results.keys():
            dimension_wise_comparison.append(self.results[key] < other.results[key])

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

    def __gt__(self, other: Configuration) -> bool:
        """
        Returns True, if 'self' > 'compared_configuration'. Otherwise - False
        :param other: instance of Configuration class
        :return: bool
        """
        return other.__lt__(self)

    def _is_valid_configuration(self, parameters):
        """
         Is parameters equal to instance parameters
        :param parameters: list
        :return: bool
        """
        if parameters == self.hyperparameters:
            return True
        else:
            self.logger.error('New configuration %s does not match with current configuration %s'
                              % (parameters, self.hyperparameters))
            return False

    def _assemble_tasks_results(self) -> Configuration:
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
        ok_tasks_results = pd.DataFrame(results_tuples, columns=self.TaskConfiguration["ResultStructure"])
        self.results = OrderedDict(ok_tasks_results.mean())
        self._standard_deviation = ok_tasks_results.std().to_list()
        self._task_amount = len(results_tuples)
        return self

    def __repr__(self):
        """
        String representation of Configuration object.
        """
        return "Configuration(Hyperparameters={params}, Tasks={num_of_tasks}, Outliers={num_of_outliers}, " \
               "Results={avg_res}, STD={std})".format(
            params=str(dict(self.hyperparameters)),
            num_of_tasks=len(self._tasks),
            num_of_outliers=len(self._tasks) - self._task_amount,
            avg_res=str(dict(self.results)),
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
            assert set(self.TaskConfiguration['ResultStructure']) <= set(task['result'].keys()), \
                f"All required result fields are not obtained. " \
                f"Expected: {self.TaskConfiguration['ResultStructure']}. Got: {task['result'].keys()}."
            return True
        except AssertionError as error:
            logging.getLogger(__name__).error("Unable to add Task (%s) to Configuration. Reason: %s" % (task, error))
            return False
