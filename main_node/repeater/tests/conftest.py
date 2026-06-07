from unittest.mock import MagicMock
from repeater.acceptable_error_based import AcceptableErrorBasedType
from core_entities.configuration import Configuration
from repeater.repeater_selector import RepeaterOrchestration
from tools.mongo_dao import MongoDB

import logging
import os
import pytest
import json

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
def mock_repeator_selection(monkeypatch):
    def mock_repeater0(self, body):
        return json.loads(body)
    monkeypatch.setattr('repeater.repeater_selector.RepeaterOrchestration._decode_for_measure_configurations', mock_repeater0)

    def mock_repeater1(self, configuration: Configuration, result):
        return 
    monkeypatch.setattr('repeater.repeater_selector.RepeaterOrchestration._send_configuration_and_tasks', mock_repeater1)
    
    def mock_repeater2(self, configuration: Configuration, tasks_to_send: list, needed_tasks_count: int):
        return configuration, needed_tasks_count

    monkeypatch.setattr('repeater.repeater_selector.RepeaterOrchestration._publish_configuration', mock_repeater2)

    # Add experiment to RepeaterOrchestration after init
    original_init_rep_orc = RepeaterOrchestration.__init__
    def new_init_rep_orc(self, experiment_id: str):
        original_init_rep_orc(self, experiment_id)
    monkeypatch.setattr('repeater.repeater_selector.RepeaterOrchestration.__init__', new_init_rep_orc)

    # Add experiment to AcceptableErrorBasedType after init
    original_init_acc_err = AcceptableErrorBasedType.__init__
    def new_init_acc_err(self, experiment_description: dict, experiment_id: str):
        original_init_acc_err(self, experiment_description, experiment_id)
    monkeypatch.setattr('repeater.acceptable_error_based.AcceptableErrorBasedType.__init__', new_init_acc_err)

@pytest.fixture(autouse=True)
def mock_event_service(monkeypatch):
    mock_connection_instance = MagicMock()
    mock_connection_instance.channel = MagicMock()
    monkeypatch.setattr('repeater.repeater_selector.RepeaterOrchestration._EventServiceConnection', MagicMock(return_value=mock_connection_instance))
