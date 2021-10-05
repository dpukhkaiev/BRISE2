import logging

class MTLBase:
    def get_data(self, input_data: dict, transferred_data: dict):
        return transferred_data

    def construct_transferred_data(self, input_data: dict, transferred_data: dict):
        return transferred_data

    def multi_task_learning(self, input_data, transferred_data):
        result = self.construct_transferred_data(input_data, transferred_data)
        return result

    def update_similar_experiments(self, input_data):
        pass


class MultiTaskLearning(MTLBase):
    def __init__(self, decorator, name, experiment_description: dict, experiment_id):
        self.decorator = decorator
        self.logger = logging.getLogger(name)
        self.experiment_description = experiment_description
        self.experiment_id = experiment_id
        self.similar_experiments = []
        self.objectiveToCompare = self.experiment_description["TaskConfiguration"]["Objectives"][
            self.experiment_description["TaskConfiguration"]["ObjectivesPriorities"].index(
                max(self.experiment_description["TaskConfiguration"]["ObjectivesPriorities"]))]
        self.isMinimizationExperiment = self.experiment_description["TaskConfiguration"]["ObjectivesMinimization"][
            self.experiment_description["TaskConfiguration"]["ObjectivesPriorities"].index(
                max(self.experiment_description["TaskConfiguration"]["ObjectivesPriorities"]))]

    def construct_transferred_data(self, input_data: dict, transferred_data: dict):
        transferred_data = self.get_data(input_data, transferred_data)
        transferred_data = self.decorator.construct_transferred_data(input_data, transferred_data)
        return transferred_data

    def update_similar_experiments(self, input_data):
        self.similar_experiments = input_data
        self.decorator.update_similar_experiments(input_data)
