from abc import ABC, abstractmethod
import logging

from core_entities.configuration import Configuration


class Repeater(ABC):
    def __init__(self, WorkerServiceClient, experiment):

        self.WSClient = WorkerServiceClient
        self.current_measurement = {}
        self.current_measurement_finished = False
        self.performed_measurements = 0
        self.feature_names = experiment.description["DomainDescription"]["FeatureNames"]
        self.max_repeats_of_experiment = experiment.description["ExperimentsConfiguration"]["MaxRepeatsOfExperiment"]

        self.logger = logging.getLogger(__name__)

        self.task_id = 0       # should be deleted, receive from WSClient
        self.worker = "alpha"  # should be deleted, receive from WSClient

    @abstractmethod
    def decision_function(self, experiment, point, iterations=3, **configuration): pass
    
    def measure_task(self, experiment, task, io, **decis_func_config):
        """
        :param experiment: the instance of Experiment class
        :param task: List of lists.
                Represents set of tasks for Worker Service. Each sublist of original task list is a final configuration
            for target system. For example, for energy consumption experiments, system configures with concrete
            frequency and threads values (e.g. frequency - 2900 MHz, threads - 3).
                So, if configuration structure defined as [frequency, threads], task object with 3 different
            configurations will be like:
            [[1800.0, 32], [2000.0, 16], [2900.0, 8]]

        :param io: Web API object.
                Used to emit information messages to front-end.
        :return: List of lists.
                Results formatted according to configured structure. E.g. if required result structure is
            [frequency, threads, energy], the result for task above will be like:
            [[1800.0, 32, 1231.1], [2000.0, 16, 5121.32], [2900.0, 8, 1215.12]]
        """
        # Removing previous measurements
        self.current_measurement.clear()
        self.current_measurement_finished = False
        # Creating holders for current measurements
        for point in task:
            # Evaluating decision function for each point in task
            self.current_measurement[str(point)] = {'data': point,
                                                    'Finished': False}
            result = self.decision_function(experiment, point, **decis_func_config)
            if result: 
                self.current_measurement[str(point)]['Finished'] = True
                self.current_measurement[str(point)]['Results'] = result

        # Continue to make measurements while decision function will not terminate it.

        while not self.current_measurement_finished:

            # Selecting only that tasks that were not finished.
            cur_task = []
            for point in self.current_measurement.keys():
                if not self.current_measurement[point]['Finished']:
                    cur_task.append(self.current_measurement[point]['data'])
                    self.performed_measurements += 1

            if not cur_task:
                self.current_measurement_finished = True
                break

            # Send this task to Worker service
            results = self.WSClient.work(cur_task)

            # Writing data to experiment.
            for point, result in zip(cur_task, results):

                configuration_object = experiment.get(configuration=point)
                if configuration_object:
                    configuration_object.put(point, str(self.task_id), result, self.worker)
                else:
                    configuration_object = Configuration()
                    configuration_object.put(point, str(self.task_id), result, self.worker)
                    experiment.put(configuration_instance=configuration_object)
                self.task_id += 1


            # Evaluating decision function for each point in task
            for point in cur_task:
                result = self.decision_function(experiment, point, **decis_func_config)
                if result:
                    self.logger.info("Point %s finished after %s measurements. Result: %s"
                                     % (str(point), len(experiment.get(point).data),
                                        str(experiment.get(point).average_result)))
                    if io:
                        temp = {
                            'configuration': self.point_to_dictionary(point), 
                            'result': list(set(result) - set(point)).pop()
                        } 
                        io.emit('task result', temp)
                    self.current_measurement[str(point)]['Finished'] = True
                    self.current_measurement[str(point)]['Results'] = result

        results_configurations = []
        for point in task:
            results_configurations.append(experiment.get(configuration=point))
        return results_configurations
    
    def cast_results(self, results):
        """
           Results formatted according to configured data types. These done because Worker Service returns all fields
           as strings, integers / floats / string differentiation is not supported.
        :param results: List of lists.
            Example, if required structure is [float, int, str], the result for task above will be like:
            [[1800.0, 32, "1231.1"], [2000.0, 16, "5121.32"], [2900.0, 8, "1215.12"]]
        :return:
        """
        # WSClient during initialization stores data types in himself, need to cast results according to that data types
        return_for_main = []
        for point in results:
            return_for_main.append(eval(self.WSClient._results_data_types[index])(value)
                                   for index, value in enumerate(point))
        return return_for_main

    def calculate_config_average(self, point_results):
        """
            Summary of all Results. Calculating avarage result for task
        :param point_results: List of all results(list) in specific point(configuration)
                    shape - list, e.g. ``[[465], [246.423]]``
        :return: List with 1 average value.
        """
        result = [0 for x in range(len(point_results[0]))]
        for experiment in point_results:
            for index, value in enumerate(experiment):
                # If the result has not digital values, we should assign this values to the result variable without averaging
                if type(value) not in [int, float]:
                    result[index] = value
                else:
                    result[index] += value
        # Calculating average.
        for index, value in enumerate(result):
            # If the result has not digital values, we should assign this values to the result variable without averaging
            if type(value) not in [int, float]:
                result[index] = value
            else:
                result[index] = eval(self.WSClient._result_data_types[index])(round(value / len(point_results), 3))
        return result

    def point_to_dictionary(self, point):
        """
            Transform list of features values to dict
        :param point: concrete experiment configuration that is evaluating
                      shape - list, e.g. ``[1200, 32]``
        :return: Dict with keys - feature name and value - value of this feature.
        """
        dict_point = dict()
        for i in range(0, len(point)):
            dict_point[self.feature_names[i]] = point[i]
        return dict_point
