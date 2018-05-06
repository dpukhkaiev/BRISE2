import logging


class Repeater:

    def __init__(self, WorkerServiceClient):

        self.WSClient = WorkerServiceClient
        self.history = History()
        self.current_measurement = {}
        self.current_measurement_finished = False
        self.available_decision_functions = {
            'brute_decision': self.brute_decition,
            'student_deviation': self.student_deviation
        }
        self.performed_measurements = 0

    def measure_task(self, task, decision_function, **configuration):

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
            # Evaluating decision function for each point in task
            self.current_measurement[str(point)] = {'data': point,
                                                    'Finished': False}
            result = decision_function(self.history, point, **configuration)
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

        results = []
        for point in task:
            results.append(self.current_measurement[str(point)]['Results'])
        return results




    def brute_decition(self, history, point, iterations = 10, **configuration):
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
                result[index] = round(value / len(all_experiments), 2)

            return result

    def student_deviation(self, history, point, threshold=15, **configuration):
        import numpy as np

        # Preparing configuration
        params = configuration.keys()

        threshold = configuration['threshold'] if 'threshold' in params else threshold
        default_point = configuration['default_point'] if 'default_point' in params else None

        # For trusted probability 0.95
        student_coeficients = {
            2: 12.7,
            3: 4.30,
            4: 3.18,
            5: 2.78,
            6: 2.57,
            7: 2.45,
            8: 2.36,
            9: 2.31,
            10: 2.26,
            11: 1.96
        }

        # first of all - need at least 2 measurements
        all_experiments = history.get(point)
        if len(all_experiments) < 2:
            return False
        else:

            # Calculating average for all dimensions
            all_experiments_np = np.matrix(all_experiments)
            all_dim_avg = all_experiments_np.mean(0)

            # Calculating standard deviation (середнє квадратичне відхилення)
            all_dim_sko = np.std(all_experiments_np, axis=0)

            # Pick the Student's coefficient, if number of experiments is 11 or more - pick coefficient for 11
            student_coeficient = student_coeficients[len(all_experiments) if len(all_experiments) < 11 else 11]

            # Calculating confidence interval for each dimension
            conf_interval = [student_coeficient * dim_sko / pow(len(all_experiments), 0.5) for dim_sko in all_dim_sko]

            # Calculating relative error for each dimension
            relative_errors = [interval / avg * 100 for interval, avg in zip(conf_interval, all_dim_avg)][0].tolist()[0]

            # Verifying that deviation of errors in each dimmension is
            for index, error in enumerate(relative_errors):
                # If for any dimension relative error is > that threshold - abort
                # print("student_deviation - need more: %s" % str(relative_errors))
                if error > threshold:
                    return False
            # print(all_dim_avg.tolist()[0])
            result = [round(x, 2) for x in all_dim_avg.tolist()[0]]
            print("Point %s finished after %s measurements. Result: %s" % (str(point), len(all_experiments), str(result)))
            return result

class History:
    def __init__(self):
        self.history = {}

    def get(self, point):
        try:
            return  self.history[str(point)]
        except KeyError:
            return {}

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

