import logging

from transfer_learning.model_recommendation.metrics.metric_abs import ModelPerformanceMetric

class AverageRelativeImprovementMetric(ModelPerformanceMetric):

    def __init__(self, isMinimizationExperiment):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.isMinimizationExperiment = isMinimizationExperiment

    def compute(self, improvement_curve: list, prediction_infos: list, start_index: int, end_index: int, multi_model: bool):
        """
        Computes average relative improvement metric to evaluate the performance of models' combination
        RI_avg = [(f_i - f_i+k)/(f_i)]/k
        :param improvement_curve: list of best objective values at each iteration (i.e., improvement curve)
        :param prediction_infos: list. Information about made prediction for each sample
        :param start_index: int. From which iteration the model should be evaluated
        :param end_index: int. To which iteration the model should be evaluated
        :param multi_model: boolean. Whether multiple models' combinations were used on interval [start_index - end_index]
        :return: dict (models' combination with its relative improvement)
        """
        if len(improvement_curve) <= end_index:
            end_index = len(improvement_curve) - 1
            if start_index >= end_index:
                return {"Model_combination": None, "relative_improvement": None}
        # multi-model tolerance
        combinations = []
        start_indices_for_combinations = []
        for i, prediction_info in enumerate(prediction_infos[start_index:end_index]):
            # if prediction was used to get configuration
            if prediction_info is not None:
                print(prediction_info)
                multi_model_flag = True
                models = []
                # if models were used and successfully built on all levels
                for part in prediction_info:
                    models.append(part["Model"])
                    if part["Model"] is None or part["time_to_build"] is None:
                        multi_model_flag = False
                if multi_model_flag is True:
                    # if new combination appears (combination changes compared to the previous iteration)
                    if len(combinations) == 0 or combinations[-1] != models:
                        combinations.append(models)
                        start_indices_for_combinations.append(start_index + i)
        try:
            if len(combinations) > 0:
                if multi_model is True:
                    improvements = []
                    for j, _ in enumerate(start_indices_for_combinations):
                        if j + 1 < len(start_indices_for_combinations):
                            if self.isMinimizationExperiment:
                                relative_improvement = (abs(improvement_curve[start_indices_for_combinations[j]])
                                                        - abs(improvement_curve[start_indices_for_combinations[j+1]])) / \
                                    abs(improvement_curve[start_indices_for_combinations[j]])
                            else:
                                relative_improvement = (abs(improvement_curve[start_indices_for_combinations[j+1]])
                                                        - abs(improvement_curve[start_indices_for_combinations[j]])) / \
                                    abs(improvement_curve[start_indices_for_combinations[j+1]])
                            improvements.append({"Model_combination": combinations[j],
                                                 "relative_improvement": relative_improvement/(start_indices_for_combinations[j+1]
                                                                                               - start_indices_for_combinations[j])})
                        # for the case when the same single model was used on the interval
                        elif j + 1 == len(start_indices_for_combinations):
                            if self.isMinimizationExperiment:
                                relative_improvement = (abs(improvement_curve[start_indices_for_combinations[j]])
                                    - abs(improvement_curve[end_index])) / \
                                    abs(improvement_curve[start_indices_for_combinations[j]])
                            else:
                                relative_improvement = (abs(improvement_curve[end_index])
                                                        - abs(improvement_curve[start_indices_for_combinations[j]])) / \
                                    abs(improvement_curve[end_index])
                            improvements.append({"Model_combination": combinations[j],
                                                 "relative_improvement": relative_improvement/(end_index -
                                                                                               start_indices_for_combinations[j])})
                    if len(improvements) > 0:
                        return max(improvements, key=lambda x: x["relative_improvement"])
                else:
                    return {"Model_combination": combinations[0],
                            "relative_improvement": ((abs(improvement_curve[start_index])
                                                      - abs(improvement_curve[end_index])) / abs(improvement_curve[start_index]))}
        except ZeroDivisionError:
            self.logger.debug("Couldn't calculate relative improvement for considered similar experiment (division by zero)!")
        return {"Model_combination": None, "relative_improvement": None}
