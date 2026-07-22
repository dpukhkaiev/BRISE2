from unittest.mock import MagicMock
from repeater.acceptable_error_based import AcceptableErrorBasedType
from core_entities.configuration import Configuration
from repeater.repeater_selector import RepeaterOrchestration

import pytest
import json

@pytest.fixture(autouse=True)
def mock_db(db_client_instance, monkeypatch):
    db_client_instance.cleanup_database()
    # Patch testDatabase
    monkeypatch.setattr('repeater.repeater_selector.MongoDB', lambda *args, **kwargs: db_client_instance)
    monkeypatch.setattr('repeater.repeater.MongoDB', lambda *args, **kwargs: db_client_instance)
    yield db_client_instance

@pytest.fixture(autouse=True)
def mock_repeater_selection(monkeypatch):
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
