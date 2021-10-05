import datetime

from transfer_learning.model_recommendation.metrics.selector import get_metric
from transfer_learning.model_recommendation.decorator import ModelRecommendationModule


class DynamicModelsRecommendation(ModelRecommendationModule):
    def __init__(self, decorator, experiment_description: dict):
        super().__init__(decorator, __name__, experiment_description)
        self.experiment_description = experiment_description
        self.isMinimizationExperiment = self.experiment_description["TaskConfiguration"]["ObjectivesMinimization"][
            self.experiment_description["TaskConfiguration"]["ObjectivesPriorities"].index(
                max(self.experiment_description["TaskConfiguration"]["ObjectivesPriorities"]))]
        self.recommendation_granularity = self.experiment_description["TransferLearning"][
            "ModelsRecommendation"]["DynamicModelsRecommendation"]["RecommendationGranularity"]
        self.time_to_build_model_threshold = datetime.timedelta(**{
            self.experiment_description["TransferLearning"]["ModelsRecommendation"][
                "DynamicModelsRecommendation"]["TimeUnit"]:
            self.experiment_description["TransferLearning"]["ModelsRecommendation"][
                "DynamicModelsRecommendation"]["TimeToBuildModelThreshold"]
        }).total_seconds()
        self.threshold_type = self.experiment_description["TransferLearning"]["ModelsRecommendation"][
            "DynamicModelsRecommendation"]["ThresholdType"]
        self.was_model_recommended = False
        self.performance_metric = get_metric(self.experiment_description, self.isMinimizationExperiment)

    def get_data(self, input_data: dict, transferred_data: dict):
        """
        Recommends the best of the available source models' combinations by time and performance criteria
        :param current_iteration: number of current iteration of the experiment
        :return: dict (models' combination)
        """
        if not self.was_model_recommended:
            if 'CurrentIteration' in input_data.keys():
                current_iteration = input_data['CurrentIteration']
            else:
                raise KeyError('No key CurrentIteration present in the input data.')
            if self.recommendation_granularity != "inf":
                if current_iteration % self.recommendation_granularity != 0:
                    transferred_data.update({"Recommended_models": None})
                    return transferred_data
            else:
                self.was_model_recommended = True
            experiments_with_model_metrics = []
            imp_start_index = current_iteration
            imp_end_index = current_iteration + float(self.recommendation_granularity)
            multi_model = True
            time_start_index = current_iteration
            time_end_index = current_iteration + float(self.recommendation_granularity)
            for experiment in self.similar_experiments:
                prediction_infos = [sample["prediction_info"] for sample in experiment["Samples"]]
                improvement_curve = experiment["Improvement_curve"]
                if self.recommendation_granularity == 1:
                    imp_start_index = current_iteration-1
                    imp_end_index = current_iteration
                    multi_model = False
                elif self.recommendation_granularity == "inf":
                    imp_start_index = 0
                    imp_end_index = len(improvement_curve) - 1
                    time_start_index = 0
                    time_end_index = len(improvement_curve) - 1
                metric = self.performance_metric.compute(improvement_curve,
                                                         prediction_infos,
                                                         imp_start_index,
                                                         int(imp_end_index),
                                                         multi_model)
                experiments_with_model_metrics.append({"Experiment": experiment,
                                                       "metric": metric,
                                                       "avg_time":
                                                       self.__get_average_time_to_build_models(metric["Model_combination"],
                                                                                               prediction_infos,
                                                                                               time_start_index,
                                                                                               int(time_end_index))})
            sorted_experiments_by_metric = \
                sorted(filter(lambda experiment_with_metric:
                              experiment_with_metric["metric"]["relative_improvement"] is not None,
                              experiments_with_model_metrics),
                       key=lambda experiment: experiment["metric"]["relative_improvement"],
                       reverse=True)
            filtered_experiments_by_time = list(filter(lambda experiment:
                                                       (experiment["avg_time"][level] is not None for level in experiment["avg_time"].keys()),
                                                       sorted_experiments_by_metric))

            i = 0
            resulting_best_combination = None
            while i < len(filtered_experiments_by_time):
                if self.threshold_type == "soft":
                    # If improvement is still good (better than average) - check time thresholds.
                    # If improvement is bad, rather take the most performant one
                    avg_imp = sum([experiment["metric"]["relative_improvement"]
                                   for experiment in filtered_experiments_by_time])/len(filtered_experiments_by_time)
                    if filtered_experiments_by_time[i]["metric"]["relative_improvement"] >= avg_imp and \
                            filtered_experiments_by_time[i]["metric"]["relative_improvement"] > 0:
                        threshold_flag = True
                        for level in filtered_experiments_by_time[i]["avg_time"].keys():
                            if filtered_experiments_by_time[i]["avg_time"][level] < self.time_to_build_model_threshold:
                                threshold_flag = False
                        if threshold_flag is True:
                            self.logger.debug(
                                f"Recommended combination of models with performance \
                                    {filtered_experiments_by_time[i]['metric']['relative_improvement']} is: \
                                    {filtered_experiments_by_time[i]['metric']['Model_combination']}")
                            resulting_best_combination = filtered_experiments_by_time[i]["metric"]["Model_combination"]
                            break
                        else:
                            self.logger.debug(
                                f"Combination {filtered_experiments_by_time[i]['metric']['Model_combination']} has a good performance \
                                    ({filtered_experiments_by_time[i]['metric']['relative_improvement']}), but violates the time threshold \
                                        {self.time_to_build_model_threshold} seconds")
                            i += 1
                    else:
                        resulting_best_combination = filtered_experiments_by_time[0]["metric"]["Model_combination"]
                        break
                else:
                    # hard threshold type (a model with violated threshold will be never recommended)
                    threshold_flag = True
                    for level in filtered_experiments_by_time[i]["avg_time"].keys():
                        if filtered_experiments_by_time[i]["avg_time"][level] < self.time_to_build_model_threshold:
                            threshold_flag = False
                    if threshold_flag is True:
                        self.logger.debug(
                            f"Recommended combination of models with performance \
                                {filtered_experiments_by_time[i]['metric']['relative_improvement']} is: \
                                {filtered_experiments_by_time[i]['metric']['Model_combination']}")
                        resulting_best_combination = filtered_experiments_by_time[i]["metric"]["Model_combination"]
                        break
                    else:
                        self.logger.debug(
                            f"Combination {filtered_experiments_by_time[i]['metric']['Model_combination']} has a good performance \
                                ({filtered_experiments_by_time[i]['metric']['relative_improvement']}), but violates the time threshold \
                                    {self.time_to_build_model_threshold} seconds")
                        i += 1
            transferred_data.update({"Recommended_models": resulting_best_combination})
            return transferred_data

    def __get_average_time_to_build_models(self, model_combination: dict,
                                           prediction_infos: list,
                                           start_index: int, end_index: int):
        """
        Computes average time to build a single model within the combination
        :param model_combination: dict. Description of a used models' combination
        :param prediction_infos: list. Information about made prediction for each sample
        :param start_index: int. From which iteration the model should be evaluated
        :param end_index: int. To which iteration the model should be evaluated
        :return: average time to build model
        """
        if len(prediction_infos) <= end_index:
            end_index = len(prediction_infos) - 1
            if start_index >= end_index:
                return None
        if model_combination is None:
            return None
        # if multiple models were used, filter out times only for previously selected combination
        considered_times_for_models = list(filter(lambda combination: (combination[i]["Model"] == model_combination[i]
                                                   and combination[i]["Model"] is not None for i in range(0, len(model_combination))),
                                                  filter(lambda info: info is not None, prediction_infos[start_index:end_index])))
        res = {}
        for level in range(0, len(model_combination)):
            times = [times_for_combination[level]["time_to_build"] for times_for_combination in
                    list(filter(lambda times_for_combination: times_for_combination[level]["time_to_build"] != 0,
                                considered_times_for_models))]
        if len(times) > 0:
            res.update({f'{level}': sum(times)/len(times)})
        if res == {}:
            return None
        else:
            return res
