from abc import ABC, abstractmethod
import logging

from tools.front_API import API


class Repeater(ABC):
    def __init__(self, WorkerServiceClient, experiment):

        self.WSClient = WorkerServiceClient
        self.current_measurement = {}
        self.current_measurement_finished = False
        self.performed_measurements = 0
        self.feature_names = experiment.description["DomainDescription"]["FeatureNames"]
        self.max_tasks_per_configuration = experiment.description["TaskConfiguration"]["MaxTasksPerConfiguration"]

        self.logger = logging.getLogger(__name__)

        self.task_id = 0       # should be deleted, receive from WSClient
        self.worker = "alpha"  # should be deleted, receive from WSClient

    @abstractmethod
    def decision_function(self, experiment, point, iterations=3, **configuration): pass
    
    def measure_configuration(self, experiment, configurations, **decis_func_config):
        """

        :param experiment: the instance of Experiment class
        :param configurations: list of instances of Configuration class

        """
        # Removing previous measurements
        self.current_measurement.clear()
        self.current_measurement_finished = False
        # Creating holders for current measurements
        for configuration in configurations:
            # Evaluating decision function for each configuration in configurations list
            self.current_measurement[str(configuration.configuration)] = {'data': configuration.configuration,
                                                                          'Finished': False}
            result = self.decision_function(experiment, configuration.configuration, **decis_func_config)
            if result: 
                self.current_measurement[str(configuration.configuration)]['Finished'] = True
                self.current_measurement[str(configuration.configuration)]['Results'] = result

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

            # Writing data to experiment.
            for task, result in zip(configurations_to_send, results):
                for config in configurations:
                    if config.configuration == task:
                        config.add_tasks(task, str(self.task_id), result, self.worker)
                        experiment.put(configuration_instance=config)
                API().send('new', 'task', configurations=[task], results=[result])
                self.task_id += 1


            # Evaluating decision function for each configuration
            for configuration in configurations_to_send:
                result = self.decision_function(experiment, configuration, **decis_func_config)
                if result:
                    temp_msg = ("Configuration %s is finished after %s measurements. Result: %s"
                                % (str(configuration), len(experiment.get(configuration).get_tasks()),
                                   str(experiment.get(configuration).get_average_result())))
                    self.logger.info(temp_msg)
                    API().send('log', 'info', message=temp_msg)
                    API().send('new', 'configuration', configurations=[configuration], results=[result])
                    self.current_measurement[str(configuration)]['Finished'] = True
                    self.current_measurement[str(configuration)]['Results'] = result
    
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
