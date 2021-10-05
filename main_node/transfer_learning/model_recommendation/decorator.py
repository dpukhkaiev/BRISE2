import logging

class MRBase:
    def get_data(self, input_data: dict, transferred_data: dict):
        return transferred_data

    def construct_transferred_data(self, input_data: dict, transferred_data: dict):
        return transferred_data

    def model_recommendation(self, input_data, transferred_data):
        result = self.construct_transferred_data(input_data, transferred_data)
        return result

    def update_similar_experiments(self, input_data):
        pass


class ModelRecommendationModule(MRBase):
    def __init__(self, decorator, name, experiment_description: dict):
        self.decorator = decorator
        self.logger = logging.getLogger(name)
        self.similar_experiments = []

    def construct_transferred_data(self, input_data: dict, transferred_data: dict):
        transferred_data = self.get_data(input_data, transferred_data)
        transferred_data = self.decorator.construct_transferred_data(input_data, transferred_data)
        return transferred_data

    def update_similar_experiments(self, input_data):
        self.similar_experiments = input_data
        self.decorator.update_similar_experiments(input_data)
