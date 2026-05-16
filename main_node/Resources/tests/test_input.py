from tools.mongo_dao import MongoDB
from unittest.mock import MagicMock

import pytest
from contextlib import ExitStack

from core_entities.experiment import Configuration
from core_entities.experiment import Experiment
from repeater.repeater_selector import RepeaterOrchestration
from repeater.quantity_based import QuantityBasedType as RMQuantityBasedType
from repeater.acceptable_error_based import AcceptableErrorBasedType
from stop_condition.stop_condition_selector import launch_stop_condition_threads
from stop_condition.bad_configuration_based import BadConfigurationBasedType
from stop_condition.guaranteed import GuaranteedType
from stop_condition.time_based import TimeBased
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

current_experiment = None

@pytest.fixture(autouse=True)
def mock_start_threads():
    """
    Mock start_threads for every Stop Condition
    """
    paths = [
        'stop_condition.validation_based.ValidationBasedType.start_threads',
        'stop_condition.time_based.TimeBased.start_threads',
        'stop_condition.quantity_based.QuantityBasedType.start_threads',
        'stop_condition.guaranteed.GuaranteedType.start_threads',
        'stop_condition.improvement_based.ImprovementBasedType.start_threads',
        'stop_condition.few_shot_learning_based.FewShotLearningBased.start_threads',
        'stop_condition.adaptive.AdaptiveType.start_threads',
        'stop_condition.bad_configuration_based.BadConfigurationBasedType.start_threads'
    ]
    
    with ExitStack() as stack:
        mocks = [stack.enter_context(patch(p, return_value=None)) for p in paths]
        yield mocks

@pytest.fixture(autouse=True)
def mock_database(monkeypatch):
    """Mock MongoDB, API, and other dependencies for input tests."""
    global current_experiment
    
    # Mock Database & get_last_record_by_experiment_id
    mock_db = MagicMock()
    def mock_get_last_record(collection, experiment_id):
        if current_experiment is None:
            return None
        if collection == "Experiment_description":
            return current_experiment.description
        if collection == "Experiment_state":
            return {
                "Current_solution": {"Results": {}},
                "Number_of_measured_configs": 0
            }
        if collection == "Search_space":
            return {"Search_space_size": current_experiment.search_space.size}
        return {}
    
    mock_db.get_last_record_by_experiment_id = mock_get_last_record
    
    # Patch MockDatabase
    monkeypatch.setattr('stop_condition.stop_condition_selector.MongoDB', lambda *args, **kwargs: mock_db)
    monkeypatch.setattr('stop_condition.stop_condition_validator.MongoDB', lambda *args, **kwargs: mock_db)
    monkeypatch.setattr('stop_condition.stop_condition.MongoDB', lambda *args, **kwargs: mock_db)
    monkeypatch.setattr('repeater.repeater_selector.MongoDB', lambda *args, **kwargs: mock_db)
    monkeypatch.setattr('repeater.repeater.MongoDB', lambda *args, **kwargs: mock_db)
    
    # Mock EventService 
    mock_connection_thread = MagicMock()
    monkeypatch.setattr('configuration_selection.configuration_selection.ConfigurationSelection._EventServiceConnection', 
                       MagicMock(return_value=mock_connection_thread))
    monkeypatch.setattr('repeater.repeater_selector.RepeaterOrchestration._EventServiceConnection',
                       MagicMock(return_value=mock_connection_thread))
    mock_connection_instance = MagicMock()
    mock_connection_instance.channel = MagicMock()
    monkeypatch.setattr('stop_condition.stop_condition_validator.EventServiceConnection', 
                        MagicMock(return_value=mock_connection_instance))
    
    # Stop Condition Validator - Mock Threading
    mock_thread_instance = MagicMock()
    monkeypatch.setattr('threading.Thread', MagicMock(return_value=mock_thread_instance))

@pytest.mark.skip(reason="Disable temporarly")
class TestInput:
    """
    Test whether all corresponding entities are created correctly. W.o. the inner functionality
    """
    def test_0(self, replace_db):
        """
        ['2 float', 'flat', 'so', 'mo.none', 'tpe', 'surr.vt.none', 'surr.ct',
        'optimizer.moea', 'opt.vt', 'opt.ct', 'validator.none', 'cs.best',
        'ted.quantity', 'mr.dynamic', 'mtl.oldnewratio', 'mtl.onlybest',
        'sc.bad', 'rm.quality', 'dch.random', 'ss.sobol']
        """
        global current_experiment
        # parse json file
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_0.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        seed_test_experiment(replace_db, experiment)

        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id,experiment=experiment)
        assert isinstance(activatedSCs[0], BadConfigurationBasedType)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id)
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


    def test_1(self, replace_db):
        """
        ['1 float 1 nom', 'flat', '2-mo', 'scalar', 'sklearn', 'surr.vt', 'surr.ct',
        'optimizer.moea', 'opt.vt.none', 'opt.ct', 'validator.quality', 'validator.internal.none' 'cs.random',
        'ted.none', 'mr.none', 'mtl.none', 'sc.time', 'rm.experiment_aware', 'dch.none', 'ss.mersenne']
        """
        global current_experiment
        # parse json file
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_1.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        seed_test_experiment(replace_db, experiment)

        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id,experiment=experiment)
        assert isinstance(activatedSCs[0], TimeBased)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id)
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


    def test_2(self, replace_db):
        """
         ['1 nom 1 float 1 nom 1 ord 1 float', 'hierarchical', '5-mo', 'pure', 'gpr-gpr',
         'surr.vt.none', 'surr.ct',  'optimizer.nsga2-moead', 'opt.ct',, 'opt.vt.none'
         'validator.quality', 'validator.internal.none' , 'cs.random',
         'ted.none', 'mr.none', 'mtl.none', 'sc.guaranteed', 'rm.quality', 'dch.random', 'ss.sobol']
        """
        global current_experiment
        # parse json file
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_2.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        seed_test_experiment(replace_db, experiment)

        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id,experiment=experiment)
        assert isinstance(activatedSCs[0], GuaranteedType)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id)
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

    def test_3(self, replace_db):
        """
         ['1 nom 1 float 1 nom 1 ord 1 float', 'flat', '5-mo', 'compositional', 'tpe', 'tpe', 'tpe', 'tpe', 'tpe',
         'surr.vt.none', 'surr.ct', 'optimizer.gaco', 'optimizer.gaco', 'optimizer.gaco',
         'optimizer.gaco', 'optimizer.gaco', 'opt.vt', 'opt.ct','validator.mock', 'validator.internal.none',
         'cs.best', 'ted.none', 'mr.none', 'mtl.none', 'sc.bad', 'rm.experiment_aware', 'dch.none', 'ss.mersenne']
        """
        global current_experiment
        # parse json file
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_3.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        seed_test_experiment(replace_db, experiment)

        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id,experiment=experiment)
        assert isinstance(activatedSCs[0], BadConfigurationBasedType)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id)
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

    def test_4(self, replace_db):
        """
        ['1 float 1 nom', 'flat', 'so', 'mo.none', 'brr', 'surr.vt.none', 'surr.ct',
        'optimizer.nsga2', 'opt.vt.none', 'opt.ct', 'validator.quality', 'validator.internal.none', 'cs.best',
        'ted.quantity', 'mr.none', 'mtl.fsl', 'sc.fsl', 'rm.experiment_aware', 'dch.none', 'ss.sobol']
        """
        global current_experiment
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_4.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        seed_test_experiment(replace_db, experiment)

        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(activatedSCs[0], FewShotLearningBased)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id)
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

    def test_5(self, replace_db):
        """
        ['2 float', 'flat', '2-mo', 'dynamic', 'mock', 'sklearn', 'sklearn', 'sklearn', 'sklearn', 'surr.vt.none',
        'surr.ct.none', 'optimizer.moead', 'opt.vt.none', 'opt.ct', 'validator.quality', 'validator.internal',
         'cs.random', 'ted.none', 'mr.none', 'mtl.none',
        'sc.time', 'rm.experiment_aware', 'dch.random', 'ss.mersenne']
        """
        global current_experiment
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_5.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        seed_test_experiment(replace_db, experiment)

        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id,experiment=experiment)
        assert isinstance(activatedSCs[0], TimeBased)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id)
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

    def test_6(self, replace_db):
        """
         ['1 float 1 nom', 'flat', '5-mo', 'pf', 'gpr', 'lr', 'mock', 'surr.vt.none',
         'surr.ct', 'optimizer.random', 'opt.vt.none', 'opt.ct','validator.quality', 'validator.internal',
         'cs.random', 'ted.none', 'mr.none', 'mtl.none', 'sc.guaranteed', 'rm.quality', 'dch.none', 'ss.mersenne']
        """
        global current_experiment
        # parse json file
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_6.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        seed_test_experiment(replace_db, experiment)

        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(activatedSCs[0], GuaranteedType)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id)
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

    def test_7(self, replace_db):
        """
         ['2 float', 'flat', '5-mo', 'pure', 'sklearn', 'surr.vt.none', 'surr.ct', 'optimizer.nsga2', 'opt.ct',
         'validator.quality', 'validator.internal.none','cs.random', 'ted.none', 'mr.none', 'mtl.none',
         'sc.guaranteed', 'rm.experiment_aware', 'dch.random', 'ss.sobol']
        """
        global current_experiment
        # parse json file
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_7.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        seed_test_experiment(replace_db, experiment)

        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(activatedSCs[0], GuaranteedType)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id)
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

    def test_8(self, replace_db):
        """
         ['1 nom 1 float 1 nom 1 ord 1 float', 'hierarchical', '2-mo', 'scalar-pf', 'mab', 'lr-gbr-brr-mock',
         'surr.vt', 'surr.ct', 'optimizer.random', 'opt.vt.none', 'opt.ct.none',
         'validator.mock-q', 'validator.internal.none-y', 'cs.best', 'ted.none',
         'mr.none', 'mtl.none', 'sc.time', 'rm.quality', 'dch.none', 'ss.sobol']
        """
        global current_experiment
        # parse json file
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_8.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        
        seed_test_experiment(replace_db, experiment)
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(activatedSCs[0], TimeBased)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id)
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

    def test_9(self, replace_db):
        """
        ['1 float 1 nom', 'flat', 'so', 'mo.none', 'mock', 'surr.vt.none', 'surr.ct.none',
        'optimizer.gaco', 'opt.vt.none', 'opt.ct',  'validator.mock', 'validator.internal.none', cs.random',
        'ted.quantity', 'mr.fsl', 'mtl.oldnewratio-fsl', 'sc.fsl', 'rm.quality', 'dch.random', 'ss.sobol']
        """
        global current_experiment
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_9.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        seed_test_experiment(replace_db, experiment)

        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(activatedSCs[0], FewShotLearningBased)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id)
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

    def test_10(self, replace_db):
        """
        ['2 float', 'flat', 'so', 'mo.none', 'gbr', 'surr.vt.none', 'surr.ct.none', 'optimizer.random',
        'opt.vt.none', 'opt.ct.none', 'validator.mock', 'validator.internal.none', 'cs.best',
        'ted.quantity', 'mr.dynamic', 'mtl.onlybest', 'sc.time', 'rm.experiment_aware', 'dch.none', 'ss.mersenne']
        """
        global current_experiment
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_10.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        seed_test_experiment(replace_db, experiment)

        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id,experiment=experiment)
        assert isinstance(activatedSCs[0], TimeBased)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id)
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

    def test_11(self, replace_db):
        """
        ['1 nom 1 float 1 nom 1 ord 1 float, 'hierarchical', 'so', 'mo.none', 'mab-brr',
        'surr.vt.none', 'surr.ct.none-y', 'optimizer.bee-gwo', 'opt.vt.none', 'opt.ct.y-none',
        'validator.mock', 'validator.internal.none', 'cs.random', 'ted.quantity', 'mr.none',
        'mtl.oldnewratio-onlybest', 'sc.guaranteed', 'rm.experiment_aware', 'dch.none', 'ss.mersenne']
        """
        global current_experiment
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_11.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        seed_test_experiment(replace_db, experiment)

        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(activatedSCs[0], GuaranteedType)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id)
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

    def test_12(self, replace_db):
        """
        ['1 nom 1 float 1 nom 1 ord 1 float', 'hierarchical', 'so', 'mo.none', 'framab-tpe',
        'surr.vt.none', 'surr.ct.none-y', 'optimizer.de-cmaes', 'opt.vt.none-af', 'opt.ct.y-none',
        'validator.mock', 'validator.internal.none', 'cs.best', 'ted.none', 'mr.fsl', 'mtl.none',
        'sc.fsl', 'rm.experiment_aware', 'dch.none', 'ss.sobol']
        """
        global current_experiment
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_12.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        seed_test_experiment(replace_db, experiment)

        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(activatedSCs[0], FewShotLearningBased)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id)
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

    def test_13(self, replace_db):
        """
        ['1 nom 1 float 1 nom 1 ord 1 float', 'flat', 'so', 'mo.none', 'brr', 'surr.vt.none', 'surr.ct',
        'optimizer.sade', 'opt.vt.none', 'opt.ct', 'validator.mock', 'validator.internal.none', 'cs.random',
        'ted.quantity', 'mr.dynamic', 'mtl.none', 'sc.bad', 'rm.experiment_aware', 'dch.none', 'ss.sobol']
        """
        global current_experiment
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_13.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        seed_test_experiment(replace_db, experiment)

        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id,experiment=experiment)
        assert isinstance(activatedSCs[0], BadConfigurationBasedType)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id)
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

    def test_14(self, replace_db):
        """
        ['2 float', 'flat', 'so', 'mo.none', 'lr', 'surr.vt.none', 'surr.ct.none',
        'optimizer.pso', 'opt.vt.none', 'opt.ct.none',  'validator.mock', 'validator.internal.none', 'cs.best',
        'ted.quantity', 'mr.fsl', 'mtl.none', 'sc.fsl', 'rm.experiment_aware', 'dch.none', 'ss.sobol']
        """
        global current_experiment
        exp_desc_file_path = './Resources/tests/test_cases_product_configurations/test_case_14.json'
        expected_experiment = "test"
        experiment_description, search_space = load_experiment_setup(exp_desc_file_path)
        assert experiment_description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # create experiment entity
        experiment = Experiment(experiment_description, search_space)
        seed_test_experiment(replace_db, experiment)

        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        assert experiment.description["Context"]["TaskConfiguration"]["TaskName"] == expected_experiment
        # launch_stop_condition_threads without threading
        activatedSCs = launch_stop_condition_threads(experiment_id=experiment.unique_id, experiment=experiment)
        assert isinstance(activatedSCs[0], FewShotLearningBased)
        # repetition management
        r = RepeaterOrchestration(experiment_id=experiment.unique_id)
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

def seed_test_experiment(db_client: MongoDB, experiment: Experiment):
    """Insert the test experiments into the database"""
    db_client.write_one_record("Experiment_description", experiment.get_experiment_description_record())
    