import pickle
from transfer_learning.model_recommendation.decorator import ModelRecommendationModule


class FewShot(ModelRecommendationModule):
    def __init__(self, decorator, experiment_description: dict):
        super().__init__(decorator, __name__, experiment_description)
        self.was_model_transferred = False

    def get_data(self, input_data: dict, transferred_data: dict):
        """
        Get the models' combination from the most similar experiment (if it is possible)
        to use it in the target experiment.
        :return: models' combination to be transferred
        """
        if self.was_model_transferred:
            transferred_data.update({"Models_to_transfer": None})
            return transferred_data
        models_to_transfer = []
        for experiment in self.similar_experiments:
            if self.were_models_dumped(experiment["Models_dumps"]):
                for model in experiment["Models_dumps"]:
                    models_to_transfer.append(pickle.loads(model))
                break
        self.was_model_transferred = True
        transferred_data.update({"Models_to_transfer": models_to_transfer})
        return transferred_data

    def were_models_dumped(self, model_dumps: list):
        were_models_dumped = True
        for model_dump in model_dumps:
            if model_dump is None:
                were_models_dumped = False
        return were_models_dumped
