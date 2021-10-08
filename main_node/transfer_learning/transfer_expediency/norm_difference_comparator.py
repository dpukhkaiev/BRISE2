from transfer_learning.transfer_expediency.comparator_abs import Comparator


class NormDifferenceComparator(Comparator):

    def __init__(self, experiment_description: dict, experiment_id: str):
        super().__init__(experiment_description, experiment_id)

    def get_source_and_target_labels(self, source_experiment):
        """
        Extracts the labels to be compared for the source and target experiments (samples, meta-feature values, etc.)
        :return: list: source_labels and target_labels
        """
        source_labels = []
        target_labels = []
        try:
            measured_configurations = self.database.get_records_by_experiment_id("Configuration", self.experiment_id)
            for config in source_experiment["Samples"]:
                for measured_config in measured_configurations:
                    if config["parameters"] == measured_config["Parameters"]:
                        target_labels.append(dict(measured_config["Results"])[self.objectiveToCompare])
                        source_labels.append(config["result"][self.objectiveToCompare])
        except KeyError:
            self.logger.debug("Some experiment-records in the database are corrupted (experiments were probably not completed)")
        return source_labels, target_labels

    def compute_metric(self, source_labels: list, target_labels: list):
        """
        The relatednes between the source and the target experiments is defined by the norm of their difference function,
        based on the metric proposed in: https://link.springer.com/chapter/10.1007/978-3-319-97304-3_4

        :return: float: average norm difference
        """
        sum_norm_dirrefences = 0

        for j, _ in enumerate(target_labels):
            sum_norm_dirrefences += pow(target_labels[j] - source_labels[j], 2)
        return sum_norm_dirrefences / len(target_labels)
