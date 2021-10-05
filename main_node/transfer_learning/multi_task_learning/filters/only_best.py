from transfer_learning.multi_task_learning.filters.decorator import Filter


class OnlyBest(Filter):
    def __init__(self, decorator):
        super().__init__(decorator, __name__)
        self.was_config_directly_transferred = False

    def filter_data(self, input_data, transferred_data: dict):
        """
        Filters configurations better than average.
        :return: Filtered configurations.
        """
        all_samples = transferred_data["Data"]
        avg_objective_value = sum(sample["result"][input_data.objectiveToCompare] for sample in all_samples)/len(all_samples)
        if input_data.isMinimizationExperiment:
            transferred_data["Data"] = list(filter(lambda sample: sample["result"][
                input_data.objectiveToCompare] <= avg_objective_value, all_samples))
        else:
            transferred_data["Data"] = list(filter(lambda sample: sample["result"][
                input_data.objectiveToCompare] >= avg_objective_value, all_samples))
        return transferred_data
