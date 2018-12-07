from abc import ABC, abstractmethod
import logging

from repeater.history import History
from tools.front_API import API


class Repeater(ABC):
    def __init__(self, WorkerServiceClient, experiment_description):

        self.WSClient = WorkerServiceClient
        self.history = History()
        self.current_measurement = {}
        self.current_measurement_finished = False
        self.performed_measurements = 0
        self.feature_names = experiment_description["DomainDescription"]["FeatureNames"]
        self.max_tasks_per_configuration = experiment_description["TaskConfiguration"]["MaxTasksPerConfiguration"]
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def decision_function(self, point, iterations=3, **configuration): pass
    
    def measure_configuration(self, configurations, **decis_func_config):
        """

        :param configurations: List of lists.
                Represents set of configurations for Worker Service.
                Each entity is a final configuration for target system.
                For example, for energy consumption experiments, system configures with concrete
            frequency and threads values (e.g. frequency - 2900 MHz, threads - 3).
                So, if configuration structure defined as [frequency, threads], configurations object with 3 different
            configurations will be like:
            [[1800.0, 32], [2000.0, 16], [2900.0, 8]]

        :return: List of lists.
                Results formatted according to configured structure. E.g. if required result structure is
            [frequency, threads, energy], the result for configurations above will be like:
            [[1800.0, 32, 1231.1], [2000.0, 16, 5121.32], [2900.0, 8, 1215.12]]
        """
        # Removing previous measurements
        self.current_measurement.clear()
        self.current_measurement_finished = False
        # Creating holders for current measurements
        for configuration in configurations:
            # Evaluating decision function for each configuration in configurations list
            self.current_measurement[str(configuration)] = {'data': configuration,
                                                            'Finished': False}
            result = self.decision_function(configuration, **decis_func_config)
            if result: 
                self.current_measurement[str(configuration)]['Finished'] = True
                self.current_measurement[str(configuration)]['Results'] = result

        # Continue to make measurements while decision function will not terminate it.
        while not self.current_measurement_finished:

            # Selecting only that configurations that were not finished.
            configurations_to_send = []
            for point in self.current_measurement.keys():
                if not self.current_measurement[point]['Finished']:
                    configurations_to_send.append(self.current_measurement[point]['data'])
                    self.performed_measurements += 1

            if not configurations_to_send:
                self.current_measurement_finished = True
                break

            # Send this configurations to Worker service
            results = self.WSClient.work(configurations_to_send)

            # Writing data to history.
            for task, result in zip(configurations_to_send, results):
                self.history.put(task, result)
                API().send('new', 'task', configurations=[task], results=[result])

            # Evaluating decision function for each configuration
            for configuration in configurations_to_send:
                result = self.decision_function(configuration, **decis_func_config)
                if result:
                    temp_msg = ("Configuration %s is finished after %s measurements. Result: %s"
                                % (str(configuration), len(self.history.get(configuration)), str(result)))
                    self.logger.info(temp_msg)
                    API().send('log', 'info', message=temp_msg)
                    API().send('new', 'configuration', configurations=[configuration], results=[result])
                    self.current_measurement[str(configuration)]['Finished'] = True
                    self.current_measurement[str(configuration)]['Results'] = result

        results = []
        for configuration in configurations:
            results.append(self.current_measurement[str(configuration)]['Results'])
        return results
    
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

    def calculate_config_average(self, tasks_results):
        """
            Summary of all Results. Calculating avarage result for configuration
        :param tasks_results: List of all results(list) in specific point(configuration)
                    shape - list, e.g. ``[[465], [246.423]]``
        :return: List with 1 average value.
        """
        result = [0 for _ in range(len(tasks_results[0]))]
        for task_result in tasks_results:
            for index, value in enumerate(task_result):
                # If the result is not a digital value, we should use this value variable without averaging
                if type(value) not in [int, float]:
                    result[index] = value
                else:
                    result[index] += value
        # Calculating average.
        for index, value in enumerate(result):
            # If the result is not a digital value, we should use this value variable without averaging
            if type(value) not in [int, float]:
                result[index] = value
            else:
                result[index] = eval(self.WSClient._result_data_types[index])(round(value / len(tasks_results), 3))
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