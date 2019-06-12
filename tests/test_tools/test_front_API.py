import pytest

from tools.front_API import API, APIMessageBuilder


def test_api_and_build():

    class DummyAPI:
        def emit(self, *args, **kwargs): return args, kwargs

    api = API(DummyAPI())

    # Testing log messages
    message_type = "log"
    str1 = APIMessageBuilder.build(message_type, message="Verifying solution that model gave..")
    assert str1 == "Verifying solution that model gave.."

    message_subtypes = ['info', 'debug', 'error', 'warning', 'critical']
    message = "Very important log message that should not be lost."
    for subtype in message_subtypes:
        sent = api.send(message_type, subtype, message=message)
        assert sent[0][0] == 'log', 'Incorrect message type!'
        assert subtype in sent[0][1].keys(), 'Incorrect message subtype!'
        assert message == sent[0][1][subtype], 'Incorrect message body!'

    # Testing experiment messages.
    message_type = "experiment"
    str1 = APIMessageBuilder.build(message_type, global_config={"some": "json"},
                                   experiment_description={"some": "json"})
    assert str1 == {'global configuration': {'some': 'json'}, 'experiment description': {'some': 'json'}}
    global_config = {'run': 'fast!'}
    experiment_description = {'experiment': 1, 'what?': 'that!'}
    sent = api.send(message_type, 'description', global_config=global_config,
                    experiment_description=experiment_description)
    assert sent[0][0] == 'experiment', 'Incorrect message type!'
    assert 'description' in sent[0][1].keys(), 'Incorrect message subtype!'
    assert sent[0][1]['description']['global configuration'] == global_config, 'Global configuration was modified!'
    assert sent[0][1]['description']['experiment description'] == experiment_description, 'Experiment description was modified!'

    configurations = [[1900, 32]]
    results = [[64.5]]
    types_subtypes = [("default", 'configuration'),
                      ("new", 'configuration'),
                      ("new", 'task'),
                      ("predictions", 'configurations'),
                      ("final", 'configuration')]

    for type_subtype in types_subtypes:
        str1 = APIMessageBuilder.build(type_subtype[0], configurations=configurations, results=results)
        assert str1 == [{'configurations': [1900, 32], 'results': [64.5]}]
        sent = api.send(*type_subtype, configurations=configurations, results=results)
        assert sent[0][0] == type_subtype[0], 'Incorrect message type!'
        assert type_subtype[1] in sent[0][1].keys(), 'Incorrect message subtype!'
        assert list(sent[0][1].values())[0] == [{'configurations': [1900, 32], 'results': [64.5]}], 'Incorrect message body!'


def test_singleton():
    api1 = API()
    api2 = API()
    assert api1 is api2
