from transfer_learning.transfer_expediency.comparator_abs import Comparator


class RgpeComparator(Comparator):

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
        Computes ranking loss for each sample from the posterior over target points,
        based on the rank-weighted Gaussian process ensemble (RGPE) method [Feurer, Letham, Bakshy ICML 2018 AutoML Workshop]
        Original paper: https://arxiv.org/pdf/1802.02219.pdf

        :return: float: average ranking loss
        """
        rank_loss = 0

        for j, _ in enumerate(target_labels):
            for k, _ in enumerate(target_labels):
                rank_loss += (source_labels[j] < source_labels[k]) ^ (target_labels[j] < target_labels[k])
        return rank_loss / len(target_labels)
