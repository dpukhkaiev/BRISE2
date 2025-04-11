from default_config_handler.default_configuration_handler_abs import DefaultConfigurationHandler
from core_entities.experiment import Experiment
from configuration_selection.model.predictor import Predictor
from core_entities.configuration import Configuration


class RandomDefaultConfigurationHandler(DefaultConfigurationHandler):
    def __init__(self, default_configuration_handler_description: dict, experiment: Experiment):
        super().__init__(default_configuration_handler_description, experiment)
        self.predictor = Predictor(experiment.unique_id, experiment.description, experiment.search_space)

    def get_default_configuration(self) -> Configuration:
        configuration = self.predictor.predict([], True)[0]
        configuration.type = Configuration.Type.DEFAULT

        return configuration
