from repeater.history import History
from repeater.repeater_abs import Repeater
class DefaultRepeater(Repeater):
    
    def decision_function(self, history, point, iterations = 10, **configuration):
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