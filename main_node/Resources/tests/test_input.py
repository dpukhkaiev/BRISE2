import pytest

from core_entities.experiment import Configuration
from core_entities.experiment import Experiment
from repeater.repeater_selector import RepeaterOrchestration
from repeater.quantity_based import QuantityBasedType as RMQuantityBasedType
from repeater.acceptable_error_based import AcceptableErrorBasedType
from stop_condition.stop_condition_selector import launch_stop_condition_threads
from stop_condition.bad_configuration_based import BadConfigurationBasedType
from stop_condition.guaranteed import GuaranteedType
from stop_condition.time_based import TimeBased
from stop_condition.quantity_based import QuantityBasedType as SCQuantityBasedType
from stop_condition.guaranteed import GuaranteedType
from stop_condition.few_shot_learning_based import FewShotLearningBased
from configuration_selection.configuration_selection import ConfigurationSelection
from configuration_selection.model.validator.quality_validator import QualityValidator
from configuration_selection.model.validator.mock_validator import MockValidator
from default_config_handler.random_default_config_handler import RandomDefaultConfigurationHandler
from default_config_handler.default_configuration_handler_orchestrator import DefaultConfigHandlerOrchestrator
from tools.initial_config import load_experiment_setup
from transfer_learning.transfer_learning_module import TransferLearningOrchestrator
from transfer_learning.transfer_expediency_determination.sampling_landmark_based import SamplingLandmarkBased
from transfer_learning.multi_task_learning.base_mtl import BaseMTL
from transfer_learning.multi_task_learning.only_best import OnlyBestDecorator
from transfer_learning.multi_task_learning.old_new_ratio import OldNewRatioDecorator
from transfer_learning.multi_task_learning.few_shot import FewShotDecorator
from transfer_learning.model_recommendation.dynamic_model_recommendation import DynamicModelRecommendation
from transfer_learning.model_recommendation.few_shot import FewShotRecommendation


class TestInput:
    """
    Test whether all corresponding entities are created correctly. W.o. the inner functionality
    """
    def test_0(self):
        """
        ['2 float', 'flat', 'so', 'mo.none', 'tpe', 'surr.vt.none', 'surr.ct',
        'optimizer.moea', 'opt.vt', 'opt.ct', 'validator.none', 'cs.best',
        'ted.quantity', 'mr.dynamic', 'mtl.oldnewratio', 'mtl.onlybest',
        'sc.bad', 'rm.quality', 'dch.random', 'ss.sobol']
        """
        # parse json file
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_0.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id,experiment=experiment)
        assert isinstance(activatedSCs[0], BadConfigurationBasedType)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(r.get_repeater(), RMQuantityBasedType)
        # configuration selection
        cs = ConfigurationSelection(experiment)
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[0].mapping_config_transformer_parameter) == 1
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[0].value_transformers) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[0].mapping_config_transformer_parameter) == 1
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[0].value_transformers) == 1
        assert isinstance(list(cs.predictor.mapping_region_model.values())[0].external_validator, MockValidator)
        assert list(cs.predictor.mapping_region_model.values())[0].internal_validator is None

        if "DefaultConfigurationHandler" in experiment.description.keys():
            dch_o = DefaultConfigHandlerOrchestrator()
            dch = dch_o.get_default_configuration_handler(experiment)
            assert dch.default_configuration_handler_description['Type'] == 'random_default_config_handler'

        tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id, experiment_description=experiment.description)
        assert isinstance(tl.ted_module, SamplingLandmarkBased)

        assert isinstance(tl.transfer_submodules["Configuration_transfer"], OnlyBestDecorator)
        assert isinstance(tl.transfer_submodules["Configuration_transfer"].base_mtl, OldNewRatioDecorator)
        assert isinstance(tl.transfer_submodules["Configuration_transfer"].base_mtl.base_mtl, BaseMTL)
        assert isinstance(tl.transfer_submodules["Model_transfer"], DynamicModelRecommendation)


    def test_1(self):
        """
        ['1 float 1 nom', 'flat', '2-mo', 'scalar', 'sklearn', 'surr.vt', 'surr.ct',
        'optimizer.moea', 'opt.vt.none', 'opt.ct', 'validator.quality', 'validator.internal.none' 'cs.random',
        'ted.none', 'mr.none', 'mtl.none', 'sc.time', 'rm.experiment_aware', 'dch.none', 'ss.mersenne']
        """
        # parse json file
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_1.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id,experiment=experiment)
        assert isinstance(activatedSCs[0], TimeBased)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(r.get_repeater(), AcceptableErrorBasedType)
        # configuration selection
        cs = ConfigurationSelection(experiment)
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[0].mapping_config_transformer_parameter) == 1
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[0].value_transformers) == 1
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[0].mapping_config_transformer_parameter) == 1
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[0].value_transformers) == 0
        assert isinstance(list(cs.predictor.mapping_region_model.values())[0].external_validator, QualityValidator)
        assert list(cs.predictor.mapping_region_model.values())[0].internal_validator is None

        if "DefaultConfigurationHandler" in experiment.description.keys():
            dch_o = DefaultConfigHandlerOrchestrator()
            dch = dch_o.get_default_configuration_handler(experiment)
            assert dch.default_configuration_handler_description['Type'] == 'random_default_config_handler'

        assert "TransferLearning" not in experiment.description.keys()


    def test_2(self):
        """
         ['1 nom 1 float 1 nom 1 ord 1 float', 'hierarchical', '5-mo', 'pure', 'gpr-gpr',
         'surr.vt.none', 'surr.ct',  'optimizer.nsga2-moead', 'opt.ct',, 'opt.vt.none'
         'validator.quality', 'validator.internal.none' , 'cs.random',
         'ted.none', 'mr.none', 'mtl.none', 'sc.guaranteed', 'rm.quality', 'dch.random', 'ss.sobol']
        """
        # parse json file
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_2.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id,experiment=experiment)
        assert isinstance(activatedSCs[0], GuaranteedType)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(r.get_repeater(), RMQuantityBasedType)
        cs = ConfigurationSelection(experiment=experiment)
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[0].mapping_config_transformer_parameter) == 4
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[0].value_transformers) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[0].mapping_config_transformer_parameter) == 4
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[0].value_transformers) == 0
        assert isinstance(list(cs.predictor.mapping_region_model.values())[0].external_validator, QualityValidator)
        assert list(cs.predictor.mapping_region_model.values())[0].internal_validator is None

        if "DefaultConfigurationHandler" in experiment.description.keys():
            dch_o = DefaultConfigHandlerOrchestrator()
            dch = dch_o.get_default_configuration_handler(experiment)
            assert dch.default_configuration_handler_description['Type'] == 'random_default_config_handler'
        if "TransferLearning" in experiment.description.keys():
            tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id, experiment_description=experiment.description)
        assert "TransferLearning" not in experiment.description.keys()

    def test_3(self):
        """
         ['1 nom 1 float 1 nom 1 ord 1 float', 'flat', '5-mo', 'compositional', 'tpe', 'tpe', 'tpe', 'tpe', 'tpe',
         'surr.vt.none', 'surr.ct', 'optimizer.gaco', 'optimizer.gaco', 'optimizer.gaco',
         'optimizer.gaco', 'optimizer.gaco', 'opt.vt', 'opt.ct','validator.mock', 'validator.internal.none',
         'cs.best', 'ted.none', 'mr.none', 'mtl.none', 'sc.bad', 'rm.experiment_aware', 'dch.none', 'ss.mersenne']
        """
        # parse json file
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_3.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id,experiment=experiment)
        assert isinstance(activatedSCs[0], BadConfigurationBasedType)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(r.get_repeater(), AcceptableErrorBasedType)
        cs = ConfigurationSelection(experiment=experiment)
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[0].mapping_config_transformer_parameter) == 4
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[0].value_transformers) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[0].mapping_config_transformer_parameter) == 2
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[0].value_transformers) == 1
        assert isinstance(list(cs.predictor.mapping_region_model.values())[0].external_validator, MockValidator)
        assert list(cs.predictor.mapping_region_model.values())[0].internal_validator is None

        if "DefaultConfigurationHandler" in experiment.description.keys():
            dch_o = DefaultConfigHandlerOrchestrator()
            dch = dch_o.get_default_configuration_handler(experiment)
            assert dch.default_configuration_handler_description['Type'] == 'random_default_config_handler'
        if "TransferLearning" in experiment.description.keys():
            tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id, experiment_description=experiment.description)
        assert "TransferLearning" not in experiment.description.keys()

    def test_4(self):
        """
        ['1 float 1 nom', 'flat', 'so', 'mo.none', 'brr', 'surr.vt.none', 'surr.ct',
        'optimizer.nsga2', 'opt.vt.none', 'opt.ct', 'validator.quality', 'validator.internal.none', 'cs.best',
        'ted.quantity', 'mr.none', 'mtl.fsl', 'sc.fsl', 'rm.experiment_aware', 'dch.none', 'ss.sobol']
        """
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_4.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(activatedSCs[0], FewShotLearningBased)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(r.get_repeater(), AcceptableErrorBasedType)
        cs = ConfigurationSelection(experiment=experiment)
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                       0].mapping_config_transformer_parameter) == 1
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                       0].value_transformers) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[
                       0].mapping_config_transformer_parameter) == 1
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[
                       0].value_transformers) == 0
        assert isinstance(list(cs.predictor.mapping_region_model.values())[0].external_validator, QualityValidator)
        assert list(cs.predictor.mapping_region_model.values())[0].internal_validator is None

        assert "DefaultConfigurationHandler" not in experiment.description.keys()

        tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id, experiment_description=experiment.description)
        assert isinstance(tl.ted_module, SamplingLandmarkBased)
        assert tl.transfer_submodules["Configuration_transfer"].is_few_shot
        assert isinstance(tl.transfer_submodules["Configuration_transfer"].base_mtl, BaseMTL)

    def test_5(self):
        """
        ['2 float', 'flat', '2-mo', 'dynamic', 'mock', 'sklearn', 'sklearn', 'sklearn', 'sklearn', 'surr.vt.none',
        'surr.ct.none', 'optimizer.moead', 'opt.vt.none', 'opt.ct', 'validator.quality', 'validator.internal',
         'cs.random', 'ted.none', 'mr.none', 'mtl.none',
        'sc.time', 'rm.experiment_aware', 'dch.random', 'ss.mersenne']
        """
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_5.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id,experiment=experiment)
        assert isinstance(activatedSCs[0], TimeBased)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(r.get_repeater(), AcceptableErrorBasedType)
        cs = ConfigurationSelection(experiment=experiment)
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[0].mapping_config_transformer_parameter) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[0].value_transformers) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[0].mapping_config_transformer_parameter) == 1
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[0].value_transformers) == 0
        assert isinstance(list(cs.predictor.mapping_region_model.values())[0].external_validator, QualityValidator)
        assert isinstance(list(cs.predictor.mapping_region_model.values())[0].internal_validator, QualityValidator)

        if "DefaultConfigurationHandler" in experiment.description.keys():
            dch_o = DefaultConfigHandlerOrchestrator()
            dch = dch_o.get_default_configuration_handler(experiment)
            assert isinstance(dch, RandomDefaultConfigurationHandler)
        if "TransferLearning" in experiment.description.keys():
            tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id, experiment_description=experiment.description)
        assert "TransferLearning" not in experiment.description.keys()
    def test_6(self):
        """
         ['1 float 1 nom', 'flat', '5-mo', 'pf', 'gpr', 'lr', 'mock', 'surr.vt.none',
         'surr.ct', 'optimizer.random', 'opt.vt.none', 'opt.ct','validator.quality', 'validator.internal',
         'cs.random', 'ted.none', 'mr.none', 'mtl.none', 'sc.guaranteed', 'rm.quality', 'dch.none', 'ss.mersenne']
        """
        # parse json file
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_6.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(activatedSCs[0], GuaranteedType)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(r.get_repeater(), RMQuantityBasedType)
        cs = ConfigurationSelection(experiment=experiment)
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                       0].mapping_config_transformer_parameter) == 1
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                       0].value_transformers) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[
                       0].mapping_config_transformer_parameter) == 1
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[
                       0].value_transformers) == 0
        assert isinstance(list(cs.predictor.mapping_region_model.values())[0].external_validator, QualityValidator)
        assert isinstance(list(cs.predictor.mapping_region_model.values())[0].internal_validator, QualityValidator)

        assert "DefaultConfigurationHandler" not in experiment.description.keys()
        assert "TransferLearning" not in experiment.description.keys()

    def test_7(self):
        """
         ['2 float', 'flat', '5-mo', 'pure', 'sklearn', 'surr.vt.none', 'surr.ct', 'optimizer.nsga2', 'opt.ct',
         'validator.quality', 'validator.internal.none','cs.random', 'ted.none', 'mr.none', 'mtl.none',
         'sc.guaranteed', 'rm.experiment_aware', 'dch.random', 'ss.sobol']
        """
        # parse json file
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_7.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(activatedSCs[0], GuaranteedType)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(r.get_repeater(), AcceptableErrorBasedType)
        cs = ConfigurationSelection(experiment=experiment)
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                       0].mapping_config_transformer_parameter) == 1
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                       0].value_transformers) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[
                       0].mapping_config_transformer_parameter) == 1
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[
                       0].value_transformers) == 0
        assert isinstance(list(cs.predictor.mapping_region_model.values())[0].external_validator, QualityValidator)
        assert list(cs.predictor.mapping_region_model.values())[0].internal_validator is None

        if "DefaultConfigurationHandler" in experiment.description.keys():
            dch_o = DefaultConfigHandlerOrchestrator()
            dch = dch_o.get_default_configuration_handler(experiment)
            assert isinstance(dch, RandomDefaultConfigurationHandler)
        assert "TransferLearning" not in experiment.description.keys()

    def test_8(self):
        """
         ['1 nom 1 float 1 nom 1 ord 1 float', 'hierarchical', '2-mo', 'scalar-pf', 'mab', 'lr-gbr-brr-mock',
         'surr.vt', 'surr.ct', 'optimizer.random', 'opt.vt.none', 'opt.ct.none',
         'validator.mock-q', 'validator.internal.none-y', 'cs.best', 'ted.none',
         'mr.none', 'mtl.none', 'sc.time', 'rm.quality', 'dch.none', 'ss.sobol']
        """
        # parse json file
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_8.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(activatedSCs[0], TimeBased)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(r.get_repeater(), RMQuantityBasedType)
        cs = ConfigurationSelection(experiment=experiment)
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                       0].mapping_config_transformer_parameter) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                       0].value_transformers) == 1
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[
                       0].mapping_config_transformer_parameter) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[
                       0].value_transformers) == 0
        assert isinstance(list(cs.predictor.mapping_region_model.values())[0].external_validator, MockValidator)
        assert list(cs.predictor.mapping_region_model.values())[0].internal_validator is None

        assert "DefaultConfigurationHandler" not in experiment.description.keys()
        assert "TransferLearning" not in experiment.description.keys()

    def test_9(self):
        """
        ['1 float 1 nom', 'flat', 'so', 'mo.none', 'mock', 'surr.vt.none', 'surr.ct.none',
        'optimizer.gaco', 'opt.vt.none', 'opt.ct',  'validator.mock', 'validator.internal.none', cs.random',
        'ted.quantity', 'mr.fsl', 'mtl.oldnewratio-fsl', 'sc.fsl', 'rm.quality', 'dch.random', 'ss.sobol']
        """
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_9.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(activatedSCs[0], FewShotLearningBased)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(r.get_repeater(), RMQuantityBasedType)
        cs = ConfigurationSelection(experiment=experiment)
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                       0].mapping_config_transformer_parameter) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                       0].value_transformers) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[
                       0].mapping_config_transformer_parameter) == 1
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[
                       0].value_transformers) == 0
        assert isinstance(list(cs.predictor.mapping_region_model.values())[0].external_validator, MockValidator)
        assert list(cs.predictor.mapping_region_model.values())[0].internal_validator is None

        if "DefaultConfigurationHandler" in experiment.description.keys():
            dch_o = DefaultConfigHandlerOrchestrator()
            dch = dch_o.get_default_configuration_handler(experiment)
            assert isinstance(dch, RandomDefaultConfigurationHandler)
        tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id,
                                          experiment_description=experiment.description)
        assert isinstance(tl.ted_module, SamplingLandmarkBased)
        assert tl.transfer_submodules["Configuration_transfer"].is_few_shot
        assert isinstance(tl.transfer_submodules["Configuration_transfer"], FewShotDecorator)
        assert isinstance(tl.transfer_submodules["Configuration_transfer"].base_mtl, OldNewRatioDecorator)
        assert isinstance(tl.transfer_submodules["Configuration_transfer"].base_mtl.base_mtl, BaseMTL)

    def test_10(self):
        """
        ['2 float', 'flat', 'so', 'mo.none', 'gbr', 'surr.vt.none', 'surr.ct.none', 'optimizer.random',
        'opt.vt.none', 'opt.ct.none', 'validator.mock', 'validator.internal.none', 'cs.best',
        'ted.quantity', 'mr.dynamic', 'mtl.onlybest', 'sc.time', 'rm.experiment_aware', 'dch.none', 'ss.mersenne']
        """
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_10.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id,experiment=experiment)
        assert isinstance(activatedSCs[0], TimeBased)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(r.get_repeater(), AcceptableErrorBasedType)
        # configuration selection
        cs = ConfigurationSelection(experiment)
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[0].mapping_config_transformer_parameter) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[0].value_transformers) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[0].mapping_config_transformer_parameter) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[0].value_transformers) == 0
        assert isinstance(list(cs.predictor.mapping_region_model.values())[0].external_validator, MockValidator)
        assert list(cs.predictor.mapping_region_model.values())[0].internal_validator is None

        assert "DefaultConfigurationHandler" not in experiment.description.keys()

        tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id, experiment_description=experiment.description)
        assert isinstance(tl.ted_module, SamplingLandmarkBased)

        assert isinstance(tl.transfer_submodules["Configuration_transfer"], OnlyBestDecorator)
        assert isinstance(tl.transfer_submodules["Configuration_transfer"].base_mtl, BaseMTL)
        assert isinstance(tl.transfer_submodules["Model_transfer"], DynamicModelRecommendation)

    def test_11(self):
        """
        ['1 nom 1 float 1 nom 1 ord 1 float, 'hierarchical', 'so', 'mo.none', 'mab-brr',
        'surr.vt.none', 'surr.ct.none-y', 'optimizer.bee-gwo', 'opt.vt.none', 'opt.ct.y-none',
        'validator.mock', 'validator.internal.none', 'cs.random', 'ted.quantity', 'mr.none',
        'mtl.oldnewratio-onlybest', 'sc.guaranteed', 'rm.experiment_aware', 'dch.none', 'ss.mersenne']
        """
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_11.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(activatedSCs[0], GuaranteedType)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(r.get_repeater(), AcceptableErrorBasedType)
        # configuration selection
        cs = ConfigurationSelection(experiment)
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                       0].mapping_config_transformer_parameter) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                       0].value_transformers) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[
                       0].mapping_config_transformer_parameter) == 1
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[
                       0].value_transformers) == 0
        assert isinstance(list(cs.predictor.mapping_region_model.values())[0].external_validator, MockValidator)
        assert list(cs.predictor.mapping_region_model.values())[0].internal_validator is None

        assert "DefaultConfigurationHandler" not in experiment.description.keys()

        tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id,
                                          experiment_description=experiment.description)
        assert isinstance(tl.ted_module, SamplingLandmarkBased)

        assert isinstance(tl.transfer_submodules["Configuration_transfer"], OnlyBestDecorator)
        assert isinstance(tl.transfer_submodules["Configuration_transfer"].base_mtl, OldNewRatioDecorator)
        assert isinstance(tl.transfer_submodules["Configuration_transfer"].base_mtl.base_mtl, BaseMTL)
        assert tl.transfer_submodules["Model_transfer"] is None

    def test_12(self):
        """
        ['1 nom 1 float 1 nom 1 ord 1 float', 'hierarchical', 'so', 'mo.none', 'framab-tpe',
        'surr.vt.none', 'surr.ct.none-y', 'optimizer.de-cmaes', 'opt.vt.none-af', 'opt.ct.y-none',
        'validator.mock', 'validator.internal.none', 'cs.best', 'ted.none', 'mr.fsl', 'mtl.none',
        'sc.fsl', 'rm.experiment_aware', 'dch.none', 'ss.sobol']
        """
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_12.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(activatedSCs[0], FewShotLearningBased)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(r.get_repeater(), AcceptableErrorBasedType)
        cs = ConfigurationSelection(experiment=experiment)
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                       0].mapping_config_transformer_parameter) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                       0].value_transformers) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[
                       0].mapping_config_transformer_parameter) == 1
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[
                       0].value_transformers) == 0
        assert isinstance(list(cs.predictor.mapping_region_model.values())[0].external_validator, MockValidator)
        assert list(cs.predictor.mapping_region_model.values())[0].internal_validator is None

        assert "DefaultConfigurationHandler" not in experiment.description.keys()

        tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id,
                                          experiment_description=experiment.description)
        assert isinstance(tl.ted_module, SamplingLandmarkBased)
        assert tl.transfer_submodules["Configuration_transfer"] is None
        assert isinstance(tl.transfer_submodules["Model_transfer"], FewShotRecommendation)

    def test_13(self):
        """
        ['1 nom 1 float 1 nom 1 ord 1 float', 'flat', 'so', 'mo.none', 'brr', 'surr.vt.none', 'surr.ct',
        'optimizer.sade', 'opt.vt.none', 'opt.ct', 'validator.mock', 'validator.internal.none', 'cs.random',
        'ted.quantity', 'mr.dynamic', 'mtl.none', 'sc.bad', 'rm.experiment_aware', 'dch.none', 'ss.sobol']
        """
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_13.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id,experiment=experiment)
        assert isinstance(activatedSCs[0], BadConfigurationBasedType)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(r.get_repeater(), AcceptableErrorBasedType)
        # configuration selection
        cs = ConfigurationSelection(experiment)
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[0].mapping_config_transformer_parameter) == 4
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[0].value_transformers) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[0].mapping_config_transformer_parameter) == 4
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[0].value_transformers) == 0
        assert isinstance(list(cs.predictor.mapping_region_model.values())[0].external_validator, MockValidator)
        assert list(cs.predictor.mapping_region_model.values())[0].internal_validator is None

        assert "DefaultConfigurationHandler" not in experiment.description.keys()

        tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id, experiment_description=experiment.description)
        assert isinstance(tl.ted_module, SamplingLandmarkBased)

        assert tl.transfer_submodules["Configuration_transfer"] is None
        assert isinstance(tl.transfer_submodules["Model_transfer"], DynamicModelRecommendation)

    def test_14(self):
        """
        ['2 float', 'flat', 'so', 'mo.none', 'lr', 'surr.vt.none', 'surr.ct.none',
        'optimizer.pso', 'opt.vt.none', 'opt.ct.none',  'validator.mock', 'validator.internal.none', 'cs.best',
        'ted.quantity', 'mr.fsl', 'mtl.none', 'sc.fsl', 'rm.experiment_aware', 'dch.none', 'ss.sobol']
        """
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_14.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(activatedSCs[0], FewShotLearningBased)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(r.get_repeater(), AcceptableErrorBasedType)
        cs = ConfigurationSelection(experiment=experiment)
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                       0].mapping_config_transformer_parameter) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                       0].value_transformers) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[
                       0].mapping_config_transformer_parameter) == 0
        assert len(list(list(cs.predictor.mapping_region_model.values())[0].mapping_optimizer_objective.keys())[
                       0].value_transformers) == 0
        assert isinstance(list(cs.predictor.mapping_region_model.values())[0].external_validator, MockValidator)
        assert list(cs.predictor.mapping_region_model.values())[0].internal_validator is None

        assert "DefaultConfigurationHandler" not in experiment.description.keys()

        tl = TransferLearningOrchestrator(experiment_id=experiment.unique_id,
                                          experiment_description=experiment.description)
        assert isinstance(tl.ted_module, SamplingLandmarkBased)
        assert tl.transfer_submodules["Configuration_transfer"] is None
        assert isinstance(tl.transfer_submodules["Model_transfer"], FewShotRecommendation)
