from repeater.history import History
class Repeater(object):
    def __init__(self, WorkerServiceClient):

        self.WSClient = WorkerServiceClient
        self.history = History()
        self.current_measurement = {}
        self.current_measurement_finished = False
        self.performed_measurements = 0

    def measure_task(self, task, **decis_func_config):
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
                    self.current_measurement[str(point)]['Finished'] = True
                    self.current_measurement[str(point)]['Results'] = result

        results = []
        for point in task:
            results.append(self.current_measurement[str(point)]['Results'])
        return results

    def decision_function(self, history, point, iterations = 3, **configuration):
        """
        Dum approach - just repeat measurement N times, compute the average and that's all.
        :param iterations: int, number of times to repeat measurement.
        :return: result
        """

        # Getting all results from history;
        # all experiments is a list of lists of numbers: [exp1, exp2...], where exp1 = [123.1, 123.4, ...]
        all_experiments = history.get(point)
        if len(all_experiments) < iterations:
            return False
        else:
            # Summing all results
            result = [0 for x in range(len(all_experiments[0]))]
            for experiment in all_experiments:
                for index, value in enumerate(experiment):
                    result[index] += value

            # Calculating average.
            for index, value in enumerate(result):
                result[index] = eval(self.WSClient.results_data_types[index])(round(value / len(all_experiments), 2))

            return result

    def cast_results(self, results):

        # WSClient during initialization stores data types in himself, need to cast results according to that data types.
        return_for_main = []
        for point in results:
            return_for_main.append(eval(self.WSClient.results_data_types[index])(value) for index, value in enumerate(point))
        return return_for_main
