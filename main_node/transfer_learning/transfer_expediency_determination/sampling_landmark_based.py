from typing import List, Union

from transfer_learning.transfer_expediency_determination.transfer_expediency_analyser import TransferExpediencyAnalyser
from tools.reflective_class_import import reflective_class_import


class SamplingLandmarkBased(TransferExpediencyAnalyser):
    def __init__(self, ted_description: dict, experiment_id: str):
        super().__init__(ted_description, experiment_id)
        self.comparator = self._get_comparator()
        self.min_number_of_samples = ted_description[self.feature_name]["MinNumberOfSamples"]
        self.clustering_algorithm = None
        self.number_of_similar_experiments = None
        quantity_type = list(self.ted_description[self.feature_name]["ExperimentsQuantity"].keys())[0]
        if quantity_type == "AdaptiveQuantity":
            self.clustering_algorithm = self._get_clustering_algorithm()
        else:
            self.number_of_similar_experiments = (
                self.ted_description)[self.feature_name]["ExperimentsQuantity"]["FixedQuantity"]["NumberOfSimilarExperiments"]

    def _get_comparator(self):
        """
        Returns instance of experiments' comparator with provided data
        :return: comparator object
        """
        comparator_key = list(self.ted_description[self.feature_name]["Comparator"].keys())[0]
        comparator_type = self.ted_description[self.feature_name]["Comparator"][comparator_key]["Type"]
        comparator_class = reflective_class_import(class_name=comparator_type,
                                                   folder_path="transfer_learning/transfer_expediency_determination")
        return comparator_class(self.ted_description, self.experiment_id)

    def _get_clustering_algorithm(self):
        """
        Returns instance of clustering algorithm with provided data
        :return: clustering_algorithm object
        """
        clustering_key = (
            list(self.ted_description[self.feature_name]["ExperimentsQuantity"]["AdaptiveQuantity"]["Clustering"].
                 keys()))[0]
        clustering_type = (
            self.ted_description)[self.feature_name]["ExperimentsQuantity"][
            "AdaptiveQuantity"]["Clustering"][clustering_key]["Type"]
        clustering_algorithm_class = (
            reflective_class_import(class_name=clustering_type,
                                    folder_path="transfer_learning/transfer_expediency_determination/clustering"))
        return clustering_algorithm_class(
            self.ted_description[self.feature_name]["ExperimentsQuantity"]["AdaptiveQuantity"]["Clustering"][
                clustering_key])

    def analyse_experiments_similarity(self) -> Union[List, None]:
        if self.database.get_last_record_by_experiment_id("Experiment_state", self.experiment_id) is None:
            return None
        # get similar experiments
        number_of_measured_configurations = \
            self.database.get_last_record_by_experiment_id("Experiment_state", self.experiment_id)[
                "Number_of_measured_configs"]
        if number_of_measured_configurations < self.min_number_of_samples:
            return None
        elif len(self.similar_experiments) > 0:
            return self.similar_experiments

        all_source_experiments = self.database.get_all_records("Transfer_learning_info")
        source_experiments = list(
            filter(lambda exp: exp["Exp_unique_ID"] != self.experiment_id, all_source_experiments))
        sorted_similar_experiments = self.comparator.get_similar_experiments(source_experiments)

        similar_experiments = []
        if len(sorted_similar_experiments) > 0:
            if self.clustering_algorithm is not None:
                similar_experiments = (
                    self.clustering_algorithm.cluster_top_most_similar_experiments(sorted_similar_experiments))
            else:
                similar_experiments = [sorted_similar_experiments[
                                       :self.number_of_similar_experiments]]
            for source_experiment in source_experiments:
                for experiment in similar_experiments:
                    if source_experiment["Exp_unique_ID"] in str(experiment):
                        self.similar_experiments.append(source_experiment)
        if len(self.similar_experiments) > 0:
            message = "The most similar experiments are: "
            for experiment in self.similar_experiments:
                message += str(experiment["Exp_unique_ID"])
                message += "; "
            self.logger.info(message)
        else:
            self.logger.info("There are no similar experiments in the database yet! Transfer Learning can not be used")
        return self.similar_experiments
