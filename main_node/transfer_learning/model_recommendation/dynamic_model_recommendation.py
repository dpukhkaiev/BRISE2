from typing import Dict, List, Union, Tuple
import numpy as np
import pickle

from transfer_learning.model_recommendation.model_recommendation_abs import ModelRecommendation
from transfer_learning.model_recommendation.metrics.metric_orchestrator import MetricOrchestrator
from configuration_selection.model.model import Model
from core_entities.search_space import Hyperparameter
from core_entities.search_space import SearchSpace


class DynamicModelRecommendation(ModelRecommendation):
    def __init__(self, experiment_description: Dict, experiment_id):
        super().__init__(experiment_description, experiment_id)
        recommendation_granularity_type = list(self.experiment_description["TransferLearning"]
                                               ["ModelRecommendation"][self.feature_name]["RecommendationGranularity"])[0]
        self.recommendation_granularity_value = (self.experiment_description["TransferLearning"]["ModelRecommendation"]
        [self.feature_name]["RecommendationGranularity"][recommendation_granularity_type]["Value"])
        self.threshold_type = (self.experiment_description["TransferLearning"]["ModelRecommendation"][self.feature_name]
        ["ThresholdType"])
        self.time_to_build_model_threshold = (self.experiment_description["TransferLearning"]["ModelRecommendation"]
        [self.feature_name]["TimeToBuildModelThreshold"])
        self.time_unit = (self.experiment_description["TransferLearning"]["ModelRecommendation"]
        [self.feature_name]["TimeUnit"])
        # metric orchestration
        metric_orchestrator = MetricOrchestrator()
        self.objective_name = list(experiment_description["Context"]["TaskConfiguration"]["Objectives"].keys())[0]  # SO only
        is_minimization = experiment_description["Context"]["TaskConfiguration"]["Objectives"][self.objective_name][
            "Minimization"]
        self.performance_metric = (metric_orchestrator.get_metric(self.experiment_description[
                                                                      "TransferLearning"]["ModelRecommendation"][
                                                                      self.feature_name]["PerformanceMetric"],
                                                                  is_minimization))

        self.was_model_recommended = False

    def recommend_best_model(self, similar_experiments: List) -> Union[Dict[Tuple[Hyperparameter], Model], None]:
        """
        Recommends the best of the available source models' combinations by time and quality criteria
        :return: a mapping of region to model to be used by predictor
        """
        if not self.was_model_recommended:
            current_iteration = (self.database.get_last_record_by_experiment_id("Experiment_state", self.experiment_id)[
                "Number_of_measured_configs"])

            if self.recommendation_granularity_value != np.inf:
                if current_iteration % self.recommendation_granularity_value != 0:
                    return None
            else:
                self.was_model_recommended = True
            experiments_with_model_metrics = []
            improvement_start_index = current_iteration
            improvement_end_index = current_iteration + self.recommendation_granularity_value
            multi_model = True
            time_start_index = current_iteration
            time_end_index = current_iteration + self.recommendation_granularity_value
            for experiment in similar_experiments:
                prediction_infos = [sample["prediction_info"] for sample in experiment["Samples"]]
                improvement_curve = experiment["Current_best_curve"]  # a list of dicts
                improvement_curve = [i[self.objective_name] for i in improvement_curve]
                if self.recommendation_granularity_value == 1:
                    improvement_start_index = current_iteration-1
                    improvement_end_index = current_iteration
                    multi_model = False
                elif self.recommendation_granularity_value == np.inf:
                    improvement_start_index = 0
                    improvement_end_index = len(improvement_curve) - 1
                    time_start_index = 0
                    time_end_index = len(improvement_curve) - 1
                metric = self.performance_metric.compute(improvement_curve,
                                                         prediction_infos,
                                                         improvement_start_index,
                                                         improvement_end_index,
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
                              experiment_with_metric["metric"]["average_relative_improvement"] is not None,
                              experiments_with_model_metrics),
                       key=lambda experiment: experiment["metric"]["average_relative_improvement"],
                       reverse=True)
            filtered_experiments_by_time = (
                list(filter(lambda experiment: (experiment["avg_time"] is not None), sorted_experiments_by_metric)))

            i = 0
            resulting_best_combination = None
            while i < len(filtered_experiments_by_time):
                if self.threshold_type == "Soft":
                    # If improvement is still good (better than average) - check time thresholds.
                    # If improvement is bad, rather take the most performant one
                    avg_imp = sum([experiment["metric"]["average_relative_improvement"]
                                   for experiment in filtered_experiments_by_time])/len(filtered_experiments_by_time)
                    if filtered_experiments_by_time[i]["metric"]["average_relative_improvement"] >= avg_imp and \
                            filtered_experiments_by_time[i]["metric"]["average_relative_improvement"] > 0:
                        threshold_flag = True
                        if filtered_experiments_by_time[i]["avg_time"] >= self.time_to_build_model_threshold:
                            threshold_flag = False
                        if threshold_flag is True:
                            self.logger.info(
                                f"Recommended combination of models with performance \
                                    {filtered_experiments_by_time[i]['metric']['average_relative_improvement']} is: \
                                    {filtered_experiments_by_time[i]['metric']['Model_combination']}")
                            resulting_best_combination = filtered_experiments_by_time[i]["metric"]["Model_combination"]
                            break
                        else:
                            self.logger.info(
                                f"Combination {filtered_experiments_by_time[i]['metric']['Model_combination']} has a good performance \
                                    ({filtered_experiments_by_time[i]['metric']['average_relative_improvement']}), but violates the time threshold \
                                        {self.time_to_build_model_threshold} seconds")
                            i += 1
                    else:
                        resulting_best_combination = filtered_experiments_by_time[0]["metric"]["Model_combination"]
                        break
                else:
                    # hard threshold type (a model with a violated threshold is never recommended)
                    threshold_flag = True
                    if filtered_experiments_by_time[i]["avg_time"] >= self.time_to_build_model_threshold:
                        threshold_flag = False
                    if threshold_flag is True:
                        self.logger.info(
                            f"Recommended combination of models with performance \
                                {filtered_experiments_by_time[i]['metric']['average_relative_improvement']} is: \
                                {filtered_experiments_by_time[i]['metric']['Model_combination']}")
                        resulting_best_combination = filtered_experiments_by_time[i]["metric"]["Model_combination"]
                        break
                    else:
                        self.logger.info(
                            f"Combination {filtered_experiments_by_time[i]['metric']['Model_combination']} has a good performance \
                                ({filtered_experiments_by_time[i]['metric']['average_relative_improvement']}), but violates the time threshold \
                                    {self.time_to_build_model_threshold} seconds")
                        i += 1
            if resulting_best_combination is None:
                return None
            else:
                mapping_region_model = {}
                search_space: SearchSpace = pickle.loads(self.database.get_last_record_by_experiment_id
                                                         ("Search_space", self.experiment_id)["SearchspaceObject"])

                models_types = []
                for i in self.experiment_description["ConfigurationSelection"]["Predictor"].items():
                    if "Model" in i[0]:
                        models_types.append(i)
                for r_index_str, model_description in resulting_best_combination.items():
                    r_index = int(r_index_str)
                    mapping_region_model[search_space.regions[r_index]] = Model(models_types[r_index],
                                                                                search_space.regions[r_index],
                                                                                self.experiment_description["Context"]
                                                                                ["TaskConfiguration"]["Objectives"])
                    mapping_region_model[search_space.regions[r_index]].update_surrogates_and_optimizers(model_description["Model"])
                return mapping_region_model

    @staticmethod
    def __get_average_time_to_build_models(model_combination: dict, prediction_infos: list,
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

        # calculate average time
        times = [model["time_to_build"] for model in model_combination.values()]
        if len(times) > 0:
            return sum(times)/len(times)
        else:
            return None
