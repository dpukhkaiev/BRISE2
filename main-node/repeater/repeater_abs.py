from abc import ABC, abstractmethod
from repeater.history import History


class Repeater(ABC):
    def __init__(self, WorkerServiceClient, ExperimentsConfiguration):

        self.WSClient = WorkerServiceClient
        self.history = History()
        self.current_measurement = {}
        self.current_measurement_finished = False
        self.performed_measurements = 0
        self.max_repeats_of_experiment = ExperimentsConfiguration["MaxRepeatsOfExperiment"]
        self.number_of_measured_configs = 0

    @abstractmethod
    def decision_function(self, history, point, iterations=3, **configuration): pass
    
    def measure_task(self, task, io, **decis_func_config):
        """

        :param task:
                     TODO - shape
        :param io: id using for web-sockets
        :return: result
        """
        # Removing previous measurements
        self.current_measurement.clear()
        self.current_measurement_finished = False
        # Creating holders for current measurements
        for point in task:
            # Evaluating decision function for each point in task
            self.current_measurement[str(point)] = {'data': point,
                                                    'Finished': False}
            result = self.decision_function(self.history, point, **decis_func_config)
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

            # Writing data to history.
            for point, result in zip(cur_task, results):
                self.history.put(point, result)

            # Evaluating decision function for each point in task
            for point in cur_task:
                result = self.decision_function(self.history, point, **decis_func_config)
                if result:
                    print("Point %s finished after %s measurements. Result: %s" % (str(point),
                                                                                   len(self.history.get(point)),
                                                                                   str(result)))
                    self.number_of_measured_configs += 1

                    if io:
                        temp = {
                            'configuration': point, 
                            'result': list(set(result) - set(point)).pop(),
                            'number_of_configs': self.number_of_measured_configs
                        } 
                        io.emit('task result', temp)
                        
                    self.current_measurement[str(point)]['Finished'] = True
                    self.current_measurement[str(point)]['Results'] = result

        results = []
        for point in task:
            results.append(self.current_measurement[str(point)]['Results'])
        return results
    
    def cast_results(self, results):
        """

        :param results:
                        TODO - shape
        :return:
        """
        # WSClient during initialization stores data types in himself, need to cast results according to that data types
        return_for_main = []
        for point in results:
            return_for_main.append(eval(self.WSClient._results_data_types[index])(value)
                                   for index, value in enumerate(point))
        return return_for_main
