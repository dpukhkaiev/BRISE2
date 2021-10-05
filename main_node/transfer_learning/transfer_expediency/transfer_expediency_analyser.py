import logging
import os

from tools.mongo_dao import MongoDB
from tools.reflective_class_import import reflective_class_import


class TransferExpediencyAnalyser:
    def __init__(self, experiment_description: dict, experiment_id: str):
        self.logger = logging.getLogger(__name__)
        self.experiment_description = experiment_description
        self.experiment_id = experiment_id
        self.similar_experiments = []
        self.were_similar_experiments_found = False
        self.database = MongoDB(os.getenv("BRISE_DATABASE_HOST"),
                                os.getenv("BRISE_DATABASE_PORT"),
                                os.getenv("BRISE_DATABASE_NAME"),
                                os.getenv("BRISE_DATABASE_USER"),
                                os.getenv("BRISE_DATABASE_PASS"))

    def get_comparator(self):
        """
        Returns instance of experiments' comparator with provided data
        :return: comparator object
        """
        comparator_type = self.experiment_description["TransferLearning"]["TransferExpediencyDetermination"]["ComparatorType"]
        comparator_class = reflective_class_import(class_name=comparator_type,
                                                   folder_path="transfer_learning/transfer_expediency")
        return comparator_class(self.experiment_description, self.experiment_id)

    def get_clustering_algorithm(self):
        """
        Returns instance of clustering algorithm with provided data
        :return: clustering_algorithm object
        """
        clustering_algorithm_type = self.experiment_description["TransferLearning"][
            "TransferExpediencyDetermination"]["ClusteringAlgorithm"]
        clustering_algorithm_class = reflective_class_import(class_name=clustering_algorithm_type,
                                                             folder_path="transfer_learning/transfer_expediency/clustering")
        return clustering_algorithm_class()

    def analyse_experiments_similarity(self):
        """
        Extracts source experiments from the DB. Returns the list of similar source experiments
        :return: list of similar experiments
        """
        numb_of_measured_configurations = \
            self.database.get_last_record_by_experiment_id("Experiment_state", self.experiment_id)["Number_of_measured_configs"]
        if numb_of_measured_configurations < \
            self.experiment_description["TransferLearning"]["TransferExpediencyDetermination"]["MinNumberOfSamples"] or \
                len(self.similar_experiments) > 0:
            return self.similar_experiments
        all_source_experiments = self.database.get_all_records("TransferLearningInfo")
        source_experiments = list(filter(lambda exp: exp["Exp_unique_ID"] != self.experiment_id, all_source_experiments))
        comparator = self.get_comparator()
        sorted_similar_experiments = comparator.get_similar_experiments(source_experiments)
        similar_experiments = []
        numberOfSimilarExperiments = self.experiment_description["TransferLearning"][
            "TransferExpediencyDetermination"]["NumberOfSimilarExperiments"]
        if len(sorted_similar_experiments) > 0:
            if numberOfSimilarExperiments == "use_clustering":
                clustering_algorithm = self.get_clustering_algorithm()
                similar_experiments = clustering_algorithm.cluster_top_most_similar_experiments(sorted_similar_experiments)
            elif isinstance(numberOfSimilarExperiments, int):
                similar_experiments = [sorted_similar_experiments[:numberOfSimilarExperiments]]
            else:
                self.logger.warning("Clustering is deactivated and no correct number is specified for the 'NumberOfSimilarExperiments' \
                parameter! All available source experiments will be used for transfer!")
                similar_experiments = sorted_similar_experiments
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
