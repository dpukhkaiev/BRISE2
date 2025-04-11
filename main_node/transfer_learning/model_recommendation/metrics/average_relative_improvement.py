import logging
from typing import List, Dict
from transfer_learning.model_recommendation.metrics.metric_abs import ModelPerformanceMetric


class AverageRelativeImprovementMetric(ModelPerformanceMetric):

    def __init__(self, is_minimization_experiment: bool):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.is_minimization_experiment = is_minimization_experiment

    def compute(self, improvement_curve: List, prediction_infos: List, start_index: int, end_index: int, multi_model: bool) -> Dict:
        """
        Computes average relative improvement metric to evaluate the performance of models' combination
        RI_avg = [(f_i - f_i+k)/(f_i)]/k
        :param improvement_curve: list of the best objective values at each iteration (i.e., improvement curve)
        :param prediction_infos: list. Information about made prediction for each sample
        :param start_index: int. From which iteration the model should be evaluated
        :param end_index: int. To which iteration the model should be evaluated
        :param multi_model: boolean. Whether multiple models were used within the interval [start_index:end_index]
        :return: dict (model with its relative improvement)
        """

        # TODO Model -> Sampling -> Model situation is not treated, but the initial approach works this way
        if len(improvement_curve) <= end_index:  # adapt end index to the length of transferred data
            end_index = len(improvement_curve) - 1
            if start_index >= end_index:
                return {"Model_combination": None, "average_relative_improvement": None}
        # multi-model tolerance
        combinations = []
        start_indices_for_combinations = []
        for i, prediction_info in enumerate(prediction_infos[start_index:end_index]):
            # if model was used to predict the configuration
            if not all([len(m["Model"]) > 0 for m in prediction_info.values()]):
                continue
            # if it is the first combination or any model within the combination is not identical
            if (len(combinations) == 0 or
                    any([combinations[-1][r]["Model"] != p_i["Model"] for r, p_i in prediction_info.items()])):
                combinations.append(prediction_info)
                start_indices_for_combinations.append(start_index + i)
        try:
            if len(combinations) > 0:
                if multi_model is True:
                    improvements = []
                    for j, _ in enumerate(start_indices_for_combinations):
                        if j + 1 < len(start_indices_for_combinations):
                            if self.is_minimization_experiment:
                                relative_improvement = (abs(improvement_curve[start_indices_for_combinations[j]])
                                                        - abs(improvement_curve[start_indices_for_combinations[j+1]])) / \
                                    abs(improvement_curve[start_indices_for_combinations[j]])
                            else:
                                relative_improvement = (abs(improvement_curve[start_indices_for_combinations[j+1]])
                                                        - abs(improvement_curve[start_indices_for_combinations[j]])) / \
                                    abs(improvement_curve[start_indices_for_combinations[j+1]])
                            improvements.append({"Model_combination": combinations[j],
                                                 "average_relative_improvement":
                                                     relative_improvement /
                                                     (start_indices_for_combinations[j+1] - start_indices_for_combinations[j])})
                        # for the case when the same model combination was used on the whole interval
                        else:
                            if self.is_minimization_experiment:
                                relative_improvement = ((abs(improvement_curve[start_indices_for_combinations[j]])
                                                        - abs(improvement_curve[end_index])) /
                                                        abs(improvement_curve[start_indices_for_combinations[j]]))
                            else:
                                relative_improvement = ((abs(improvement_curve[end_index])
                                                        - abs(improvement_curve[start_indices_for_combinations[j]])) /
                                                        abs(improvement_curve[end_index]))
                            improvements.append({"Model_combination": combinations[j],
                                                 "average_relative_improvement":
                                                     relative_improvement /
                                                     (end_index - start_indices_for_combinations[j])})
                    if len(improvements) > 0:
                        return max(improvements, key=lambda x: x["average_relative_improvement"])
                else:
                    return {"Model_combination": combinations[0], "average_relative_improvement":
                        ((abs(improvement_curve[start_index]) - abs(improvement_curve[end_index])) / abs(
                            improvement_curve[start_index]))}
        except ZeroDivisionError:
            self.logger.debug("Couldn't calculate average relative improvement for considered similar experiment (division by zero)!")
        return {"Model_combination": None, "average_relative_improvement": None}
