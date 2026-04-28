import numpy as np
from typing import Dict

from sklearn.cluster import MeanShift, estimate_bandwidth
from transfer_learning.transfer_expediency_determination.clustering.clustering_algorithm import ClusteringAlgorithm


class MeanShiftClustering(ClusteringAlgorithm):
    def __init__(self, clustering_description: Dict):
        super().__init__(clustering_description)
        self.bandwidth = None
        if clustering_description["BandwidthType"] == "Estimated":
            self.quantile = clustering_description["quantile"]
        else:
            self.bandwidth = clustering_description["bandwidth"]

    def cluster_top_most_similar_experiments(self, similar_experiments: list):
        """
        Apply clustering to define an appropriate number of the most similar source experiments.
        The Mean Shift clustering algorithm is used here: https://scikit-learn.org/stable/modules/generated/sklearn.cluster.MeanShift.html
        :param similar_experiments: list
        :return: list with a defined number of the most similar experiments
        """
        x = []
        top_similar_experiments = []
        for experiment_pair in similar_experiments:
            x.append(np.asarray([experiment_pair[1], 0.0]))
        X = np.asarray(x)
        # WARNING: 'quantile' parameter affects the number of Mean Shift clusters indirectly.
        # It must be chosen wisely depending on the estimated number of experiments in the DB
        # https://stackoverflow.com/questions/28335070/how-to-choose-appropriate-quantile-value-while-estimating-bandwidth-in-meanshift
        if self.bandwidth is None:
            self.bandwidth = estimate_bandwidth(X, quantile=self.quantile)
        if self.bandwidth <= 0.0:
            self.bandwidth = 0.5
        ms = MeanShift(bandwidth=self.bandwidth, bin_seeding=True)
        ms.fit(X)
        for i, cluster in enumerate(ms.labels_):
            self.logger.debug(f"Experiment {similar_experiments[i]} - belongs to cluster {cluster}")
            if cluster == ms.labels_[0]:
                top_similar_experiments.append(similar_experiments[i])
        return top_similar_experiments
