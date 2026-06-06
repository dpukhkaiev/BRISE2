import logging
import os
import pytest

from contextlib import ExitStack
from unittest.mock import MagicMock, patch
from tools.mongo_dao import MongoDB

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

@pytest.fixture(scope="session")
def db_client_instance():
    """Initializes the database"""
    client = MongoDB(os.getenv("BRISE_DATABASE_HOST"),
                                    os.getenv("BRISE_DATABASE_PORT"),
                                    os.getenv("BRISE_DATABASE_NAME"),
                                    os.getenv("BRISE_DATABASE_USER"),
                                    os.getenv("BRISE_DATABASE_PASS"))
    return client

@pytest.fixture(autouse=True)
def replace_db(db_client_instance, monkeypatch):
    db_client_instance.cleanup_database()
    # Patch testDatabase
    monkeypatch.setattr('stop_condition.stop_condition_selector.MongoDB', lambda *args, **kwargs: db_client_instance)
    monkeypatch.setattr('stop_condition.stop_condition_validator.MongoDB', lambda *args, **kwargs: db_client_instance)
    monkeypatch.setattr('stop_condition.stop_condition.MongoDB', lambda *args, **kwargs: db_client_instance)
    monkeypatch.setattr('repeater.repeater_selector.MongoDB', lambda *args, **kwargs: db_client_instance)
    monkeypatch.setattr('repeater.repeater.MongoDB', lambda *args, **kwargs: db_client_instance)
    yield db_client_instance

@pytest.fixture(scope="module", autouse=True)
def cleanup_after_input_tests():
    """
    Remove experiments from Database after the tests are finsihed
    """
    # Setup
    yield 
    # Teardown

    try:
        db_client = MongoDB() 
        
        if hasattr(db_client, 'cleanup_database'):
            db_client.cleanup_database()
        else:
            db_client.db["Configuration"].drop()
            db_client.db["Experiment_description"].drop()
            db_client.db["Experiment_state"].drop()
            db_client.db["Search_space"].drop()
            
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to clear database during teardown: {e}")

@pytest.fixture(autouse=True)
def mock_stop_condition(monkeypatch):
    mock_thread_instance = MagicMock()
    monkeypatch.setattr('threading.Thread', MagicMock(return_value=mock_thread_instance))

@pytest.fixture(autouse=True)
def mock_event_service(monkeypatch):
    mock_connection_thread = MagicMock()
    monkeypatch.setattr('configuration_selection.configuration_selection.ConfigurationSelection._EventServiceConnection', 
                       MagicMock(return_value=mock_connection_thread))
    monkeypatch.setattr('repeater.repeater_selector.RepeaterOrchestration._EventServiceConnection',
                       MagicMock(return_value=mock_connection_thread))
    mock_connection_instance = MagicMock()
    mock_connection_instance.channel = MagicMock()
    monkeypatch.setattr('stop_condition.stop_condition_validator.EventServiceConnection', 
                        MagicMock(return_value=mock_connection_instance))
