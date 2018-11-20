import pytest

from tools.front_API import API, APIMessageBuilder

def test_build():
    message_type = "log"
    str1 = APIMessageBuilder.build(message_type, message="Verifying solution that model gave..")
    assert str1 == "Verifying solution that model gave.."
    message_type = "experiment"
    str1 = APIMessageBuilder.build(message_type, global_config={"some": "json"}, experiment_config={"some": "json"})
    assert str1 == {'global configuration': {'some': 'json'}, 'experiment configuration': {'some': 'json'}}
    message_type = "task"
    str1 = APIMessageBuilder.build(message_type, configurations=[[1900, 32]], results=[[64.5]])
    assert str1 == [{'configurations': [1900, 32], 'results': [64.5]}]
    

def test_singleton():
    api1 = API()
    api2 = API()
    assert api1 is api2
    