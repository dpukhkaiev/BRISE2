import logging


class Repeater:

    def __init__(self, WorkerServiceClient):

        self.WSClient = WorkerServiceClient
        self.history = History()
        self.current_measurement = {}
        self.current_measurement_finished = False
        self.available_decision_functions = {
            'brute_decision': self.brute_decition
        }

    def measure_task(self, task, decision_function):

        # Verifying that provided decision function is available.
        if decision_function in self.available_decision_functions.keys():
            decision_function = self.available_decision_functions[decision_function]
        else:
            print("Warning! Specified decision function \"%s\" not found, using \"%s\"")
            decision_function = self.available_decision_functions[list(self.available_decision_functions.keys())[0]]

        # Removing previous measurements
        self.current_measurement.clear()
        self.current_measurement_finished = False
        # Creating holders for current measurements
        for point in task:
            self.current_measurement[str(point)] = {'data': point,
                                                    'Finished': False}

        # Continue to make measurements while decision function will not terminate it.
        while not self.current_measurement_finished:

            # Selecting only that tasks that were not finished.
            cur_task = []
            for point in self.current_measurement.keys():
                if not self.current_measurement[point]['Finished']:
                    cur_task.append(self.current_measurement[point]['data'])

            # Send this task to Worker service
            results = self.WSClient.work(cur_task)

            if len(cur_task) != len(results):
                print("Results and task have different length: %s and %s. Need to investigate:" % (cur_task, results))
                while True:
                    exec(input(">>>"))

            # Writing data to history.
            for point, result in zip(cur_task, results):
                self.history.put(point, result)

            # Evaluating decision function for each point in task
            for point in cur_task:
                result = decision_function(self.history, point)
                if result:
                    self.current_measurement[str(point)]['Finished'] = True
                    self.current_measurement[str(point)]['Results'] = result
            print(self.history.history)


    def brute_decition(self, history, point, iterations=5):
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
            for index, value in result:
                result[index] = value / len(all_experiments)

            return result


class History:
    def __init__(self):
        self.history = {}

    def get(self, point):
        try:
            return  self.history[str(point)]
        except KeyError:
            return None

    def put(self, point, values):
        try:
            self.history[str(point)].append(values)
        except KeyError:
            self.history[str(point)] = []
            self.history[str(point)].append(values)

    def dump(self, filename):

        try:
            lines = 0
            with open(filename, "w") as f:
                for key in self.history.keys():
                    f.write(key)
                    lines += 1
            print("History dumped. Number of written points: %s" % lines)
            return True
        except Exception as e:
            print("Failed to write results. Exception: %s" % e)


if __name__ == "__main__":
    print("-" * 10 + "Testing History" + "-" * 10)
    h = History()
    p = [1,2,3]
    v = ['new', 'value', 123]
    print("getting not existing:")
    print(h.get(p))
    print(h.history)
    print("putting not existing:")
    print(h.put(p, v))
    print(h.history)
    print("getting existing:")
    print(h.get(p))
    print(h.history)
    print("putting existing:")
    print(h.put(p, v))
    print(h.history)
    print("getting existing:")
    print(h.get(p))
    print(h.history)
    print("-" * 10 + "end testing History" + "-" * 10)

