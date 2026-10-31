from core_entities.experiment import Experiment
from core_entities.configuration import Configuration
from default_config_handler.default_configuration_handler_orchestrator import DefaultConfigHandlerOrchestrator
from default_config_handler.basic_default_config_handler import BasicDefaultConfigurationHandler
from default_config_handler.random_default_config_handler import RandomDefaultConfigurationHandler


class TestDefaultConfigHandler():
    def test_random_dch_explicit_flat_search_space(self, get_experiment):
        experiment_description, search_space = get_experiment(0)
        experiment = Experiment(experiment_description, search_space)

        dch_o = DefaultConfigHandlerOrchestrator()
        default_config_handler = dch_o.get_default_configuration_handler(experiment=experiment)
        assert isinstance(default_config_handler, RandomDefaultConfigurationHandler)

        default_configuration = default_config_handler.get_default_configuration()
        assert default_configuration.type is Configuration.Type.DEFAULT

    def test_basic_dch_default_when_unspecified(self, get_experiment):
        experiment_description, search_space = get_experiment(1)
        experiment = Experiment(experiment_description, search_space)

        dch_o = DefaultConfigHandlerOrchestrator()
        default_config_handler = dch_o.get_default_configuration_handler(experiment=experiment)
        assert isinstance(default_config_handler, BasicDefaultConfigurationHandler)

        default_configuration = default_config_handler.get_default_configuration()
        assert default_configuration.type is Configuration.Type.DEFAULT

    def test_random_dch_explicit_hierarchical_search_space(self, get_experiment):
        experiment_description, search_space = get_experiment(2)
        experiment = Experiment(experiment_description, search_space)

        dch_o = DefaultConfigHandlerOrchestrator()
        default_config_handler = dch_o.get_default_configuration_handler(experiment=experiment)
        assert isinstance(default_config_handler, RandomDefaultConfigurationHandler)

        default_configuration = default_config_handler.get_default_configuration()
        assert default_configuration.type is Configuration.Type.DEFAULT

    def test_basic_dch_for_3_level_hierarchical_space(self, get_experiment):
        # test_case_15 activates N0.N02, whose two children N1 and O1 each activate their own region
        # one level down (N1.N11 -> F2, N2; O1.O11 -> I2), so that level has two regions at once, with
        # a further level (N2.N21 -> F3) nested below one of them.
        experiment_description, search_space = get_experiment(15)
        experiment = Experiment(experiment_description, search_space)

        dch_o = DefaultConfigHandlerOrchestrator()
        default_config_handler = dch_o.get_default_configuration_handler(experiment=experiment)
        assert isinstance(default_config_handler, BasicDefaultConfigurationHandler)

        default_configuration = default_config_handler.get_default_configuration()
        assert set(default_configuration.parameters.keys()) == {
            "Context.SearchSpace.N0",
            "Context.SearchSpace.N0.N02.N1",
            "Context.SearchSpace.N0.N02.N1.N11.F2",
            "Context.SearchSpace.N0.N02.N1.N11.N2",
            "Context.SearchSpace.N0.N02.N1.N11.N2.N21.F3",
            "Context.SearchSpace.N0.N02.O1",
            "Context.SearchSpace.N0.N02.O1.O11.I2",
        }

        # the N0.N01 branch (region holding F1, I1) is never activated by this default configuration,
        # so prediction_info must cover only the 5 traversed regions, not all 6 
        assert len(experiment.search_space.regions) == 6
        assert len(default_configuration.prediction_info) == 5
        assert all(v == {"Model": [], "time_to_build": 0} for v in default_configuration.prediction_info.values())
