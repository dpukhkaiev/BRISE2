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
    def decision_function(self, current_configuration, iterations=3, **configuration): pass
    
    def measure_configurations(self, experiment, configurations, **decis_func_config):
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
            self.current_measurement[str(configuration.get_parameters())] = {'data': configuration.get_parameters(),
                                                                             'Finished': False}
            result = self.decision_function(configuration, **decis_func_config)
            if result: 
                self.current_measurement[str(configuration.get_parameters())]['Finished'] = True
                self.current_measurement[str(configuration.get_parameters())]['Results'] = result

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

            # Sending data to API
            for parameters, result in zip(configurations_to_send, results):
                for config in configurations:
                    if config.get_parameters() == parameters:
                        config.add_tasks(parameters, str(self.task_id), result, self.worker)

                API().send('new', 'task', configurations=[parameters], results=[result])
                self.task_id += 1


            # Evaluating decision function for each configuration
            for configuration in configurations_to_send:
                for config in configurations:
                    if configuration == config.get_parameters():
                        result = self.decision_function(config, **decis_func_config)
                        if result:
                            temp_msg = ("Configuration %s is finished after %s measurements. Result: %s"
                                        % (str(configuration), len(config.get_tasks()),
                                           str(config.get_average_result())))
                            self.logger.info(temp_msg)
                            API().send('log', 'info', message=temp_msg)
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
