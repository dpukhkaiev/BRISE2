from core_entities.experiment import Experiment
from core_entities.configuration import Configuration
from default_config_handler.default_configuration_handler_orchestrator import DefaultConfigHandlerOrchestrator
from default_config_handler.basic_default_config_handler import BasicDefaultConfigurationHandler
from default_config_handler.random_default_config_handler import RandomDefaultConfigurationHandler


class TestDefaultConfigHandler():
    def test_0(self, get_experiment, get_workers):
        experiment_description, search_space = get_experiment(0)
        experiment = Experiment(experiment_description, search_space)

        dch_o = DefaultConfigHandlerOrchestrator()
        default_config_handler = dch_o.get_default_configuration_handler(experiment=experiment)
        assert isinstance(default_config_handler, RandomDefaultConfigurationHandler)

        default_configuration = default_config_handler.get_default_configuration()
        assert default_configuration.type is Configuration.Type.DEFAULT

    def test_1(self, get_experiment, get_workers):
        experiment_description, search_space = get_experiment(1)
        experiment = Experiment(experiment_description, search_space)


        dch_o = DefaultConfigHandlerOrchestrator()
        default_config_handler = dch_o.get_default_configuration_handler(experiment=experiment)
        assert isinstance(default_config_handler, BasicDefaultConfigurationHandler)


        default_configuration = default_config_handler.get_default_configuration()
        assert default_configuration.type is Configuration.Type.DEFAULT

    def test_2(self, get_experiment, get_workers):
        experiment_description, search_space = get_experiment(2)
        experiment = Experiment(experiment_description, search_space)

        dch_o = DefaultConfigHandlerOrchestrator()
        default_config_handler = dch_o.get_default_configuration_handler(experiment=experiment)
        assert isinstance(default_config_handler, RandomDefaultConfigurationHandler)

        default_configuration = default_config_handler.get_default_configuration()
        assert default_configuration.type is Configuration.Type.DEFAULT

