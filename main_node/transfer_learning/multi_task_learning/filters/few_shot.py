from transfer_learning.multi_task_learning.filters.decorator import Filter


class FewShot(Filter):
    def __init__(self, decorator):
        super().__init__(decorator, __name__)
        self.was_config_directly_transferred = False

    def filter_data(self, input_data, transferred_data: dict):
        """
        Returns the best configuration from the most similar source experiment
        be directly measured in the target experiment
        :return: Configuration to be directly transferred
        """
        if self.was_config_directly_transferred:
            transferred_data["Data"] = []
            return transferred_data
        if input_data.isMinimizationExperiment:
            config_to_transfer = min(input_data.similar_experiments[0]["Samples"],
                                     key=lambda x: x["result"][input_data.objectiveToCompare])
        else:
            config_to_transfer = max(input_data.similar_experiments[0]["Samples"],
                                     key=lambda x: x["result"][input_data.objectiveToCompare])
        self.was_config_directly_transferred = True
        transferred_data["Data"] = [config_to_transfer]
        transferred_data["FewShotFlag"] = True
        return transferred_data
