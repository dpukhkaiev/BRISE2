import pytest
import os

from tools.front_API import APIMessageBuilder, API
from tools.rabbit_API_class import RabbitApi

os.environ["TEST_MODE"] = 'UNIT_TEST'

class TestFrontApi:
    # this test set is aimed to cover the functionality of the 'front_API' tools and the 'singleton'

    api = API()

    def test_0_build_log_message(self):
        # Test #0. Build log message according to the API message format
        # Expected result: the message of type 'string' is built independently on its content
        expected_result = "This is log"
        msg = "This is log"
        actual_result = APIMessageBuilder.build('LOG', message=msg)
        assert actual_result == expected_result

    def test_1_build_log_message_of_multiple_parts(self):
        # Test #1. Build log message according to the API message format. Message consists of several parts
        # Expected result: the single message of type 'string' is built by concatenation
        expected_result = "This is log"
        msg1 = "This is "
        msg2 = "log"
        actual_result = APIMessageBuilder.build('LOG', message1=msg1,  message2=msg2)
        assert actual_result == expected_result

    def test_2_build_empty_log_message(self):
        # Test #2. Build log message according to the API message format. Message is empty
        # Expected result: the single empty message of type 'string' is built
        expected_result = ""
        actual_result = APIMessageBuilder.build('LOG')
        assert actual_result == expected_result

    def test_3_build_new_task_message(self):
        # Test #3. Build task message according to the API message format. The 'result' is an empty list
        # Expected result: the task message of type 'list' is built. It contains the "configuration-result" pair as a dictionary.
        expected_result = [{'configurations': [2200.0, 8], 'results': None}]
        configurations=[[2200.0, 8]]
        actual_result = APIMessageBuilder.build('NEW', configurations=configurations, results=[None])
        assert actual_result == expected_result

    def test_4_build_task_message_with_result(self):
        # Test #4. Build task message according to the API message format. Use different supported message types
        # Expected result: the task message of type 'list' is built. It contains the "configuration-result" pair as a dictionary.
        expected_result = [{'configurations': [2200.0, 8], 'results': 123}]
        configurations=[[2200.0, 8]]
        results=[123]
        message_types = ['DEFAULT', 'PREDICTIONS', 'FINAL']
        for message_type in message_types:
            actual_result = APIMessageBuilder.build(message_type, configurations=configurations, results=results)
            assert actual_result == expected_result

    def test_5_build_invalid_task_message(self):
        # Test #5. Build task message with the invalid values according to the API message format
        # Expected result: error is raised, that invalid parameters are passed
        expected_result = "Invalid parameters passed to send message via API: The configurations(key parameter) are not provided or have invalid format!"
        with pytest.raises(KeyError) as excinfo:
            APIMessageBuilder.build('NEW', configurations="Invalid string", results="Invalid string")
        assert expected_result in str(excinfo.value)

    def test_6_build_incomplete_task_message(self):
        # Test #6. Build task message with incomplete parameters (without 'results')
        # Expected result: error is raised
        configurations=[[2200.0, 8]]
        expected_result = "Invalid parameters passed to send message via API: The results(key parameter) are not provided or have invalid format!"
        with pytest.raises(KeyError) as excinfo:
            APIMessageBuilder.build('NEW', configurations=configurations)
        assert expected_result in str(excinfo.value)

    def test_7_build_inconsistent_task_message(self):
        # Test #7. Build task message with inconsistent dimensionality of 'configurations' and 'results'
        # Expected result: error is raised
        configurations=[[2200.0, 8]]
        results=[123, 234]
        expected_result = "Different sizes of provided parameters!"
        with pytest.raises(KeyError) as excinfo:
            APIMessageBuilder.build('NEW', configurations=configurations, results=results)
        assert expected_result in str(excinfo.value)

    def test_8_build_experiment_message(self):
        # Test #8. Build experiment message according to the API message format
        # Expected result: the message of type 'dictionary' is built and contains all needed fields
        from tools.initial_config import load_experiment_setup
        experiment_description, searchspace_description = \
            load_experiment_setup("./Resources/EnergyExperiment/EnergyExperiment.json")
        global_config = experiment_description["General"]
        actual_result = APIMessageBuilder.build('EXPERIMENT', global_config=global_config, experiment_description=experiment_description,
        searchspace_description=searchspace_description)
        assert actual_result["global_configuration"]
        assert actual_result["experiment_description"]
        assert actual_result["searchspace_description"]

    def test_9_build_incomplete_experiment_message(self):
        # Test #9. Build experiment message from incomplete parameters
        # Expected result: error is raised
        from tools.initial_config import load_experiment_setup
        expected_result = "Invalid parameters passed to send message via API: The search space description is not provided!"
        experiment_description, _ = load_experiment_setup("./Resources/EnergyExperiment/EnergyExperiment.json")
        global_config = experiment_description["General"]
        with pytest.raises(KeyError) as excinfo:
            APIMessageBuilder.build('EXPERIMENT', global_config=global_config, experiment_description=experiment_description)
        assert expected_result in str(excinfo.value)

    def test_10_send_valid_message(self):
        # Test #10. Send messages of all supported types and subtypes via the dummy API
        # Expected result: no errors are arised, sending is simulated
        expected_type = "log"
        expected_payload = "This is msg"
        msg = "This is msg"
        type_subtype = {}
        type_subtype["LOG"] = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]        
        for msg_type in type_subtype:
            for msg_subtype in type_subtype[msg_type]:
                expected_subtype = msg_subtype.lower()
                actual_result = TestFrontApi.api.send(msg_type, msg_subtype, message=msg)
                assert actual_result[0][0] == expected_type
                assert actual_result[0][1] == expected_subtype
                assert actual_result[0][2] == expected_payload
    
    def test_11_send_unknown_type_of_msg(self, caplog):
        # Test #11. Try to send unknown (unsupported) type of message
        # Expected result: error is raised, that message type is not supported
        expected_result = "Message type is not supported!"
        msg = "This is msg"
        TestFrontApi.api.send('DUMMY', 'INFO', message=msg)
        for record in caplog.records:
            assert record.levelname == "ERROR"
            assert expected_result in str(record)

    def test_12_send_unknown_subtype_of_msg(self, caplog):
        # Test #12. Try to send unknown (unsupported) subtype of message
        # Expected result: error is raised, that message subtype is not supported
        expected_result = "Message subtype is not supported!"
        msg = "This is msg"
        msg_types = ["LOG","NEW","DEFAULT","PREDICTIONS","FINAL","EXPERIMENT"]
        for msg_type in msg_types:
            TestFrontApi.api.send(msg_type, 'dummy', message=msg)
            for record in caplog.records:
                assert record.levelname == "ERROR"
                assert expected_result in str(record)

    def test_13_send_invalid_format_of_message(self, caplog):
        # Test #13. Try to send supported type of message, but specified in unexpected format
        # Expected result: error is raised
        expected_result = "Wrong API message type object!"
        msg = "This is msg"
        TestFrontApi.api.send(['LOG'], 'dummy', message=msg)
        for record in caplog.records:
            assert record.levelname == "ERROR"
            assert expected_result in str(record)

    def test_14_singleton_front_api(self):
        # Test #14. Try to create 2 instances of the API class
        # Expected result: only a single instance exists (due to the singleton)
        API._instance = None
        api1 = API()
        api2 = API()
        assert api1 is api2

    def test_15_singleton_front_api_different_objects(self):
        # Test #15. Try to create 2 instances of the API class, initialized with different api objects
        # Expected result: only a single instance exists (due to the singleton)
        API._instance = None
        api1 = API()
        api2 = API(api_object=RabbitApi("event-service", 49153))
        assert api1 is api2

    def test_16_api_without_emit(self):
        # Test #16. Try to create an instance of the API class, with api object without emit() method
        # Expected result: AttributeError is thrown, informing about the requirements to the api object
        class BadAPI:
            def no_emit(self):
                pass
        expected_result = "Provided API object doesn't contain 'emit()' method"
        # cleanup
        API._instance = None
        with pytest.raises(AttributeError) as excinfo:
            API(BadAPI())
        assert expected_result in str(excinfo.value)

    def test_17_api_with_wrong_emit_parameter_types(self):
        # Test #17. Try to create an instance of the API class, with wrong api object emit() parameters' types
        # Expected result: AttributeError is thrown, informing about the requirements to the api object
        class BadAPI:
            def emit(self, message_type: dict, message_subtype: dict, message: dict):
                pass
        expected_result = "Provided API object has unsupported 'emit()' method. Its parameters do not correspond to the required!" \
                "Expected parameters are: 'message_type: str', 'message_subtype: str', 'message: str'"
        # cleanup
        API._instance = None
        with pytest.raises(AttributeError) as excinfo:
            API(BadAPI())
        assert expected_result in str(excinfo.value)

    def test_18_api_with_unexpected_emit_parameter_names(self, caplog):
        # Test #18. Try to create an instance of the API class, with wrong api object emit() parameters' names
        # Expected result: object is created, but user is warned about the advisable parameters' names
        import logging
        caplog.set_level(logging.WARNING)
        class BadAPI:
            def emit(self, dummy: str, message_subtype: str, message: str):
                pass
        expected_result = "Parameter names of the emit() method are untypical for your API object. It is advisable to check emit() parameters" \
                    "Expected parameters are: 'message_type', 'message_subtype', 'message'"
        # cleanup
        API._instance = None
        API(BadAPI())
        for record in caplog.records:
            assert record.levelname == "WARNING"
            assert expected_result in str(record)

    def test_19_api_with_missing_emit_parameters(self):
        # Test #19. Try to create an instance of the API class, with missing api object emit() parameters
        # Expected result: AttributeError is thrown, informing about the requirements to the api object
        class BadAPI:
            def emit(self, message_type: str, message_subtype: str):
                pass
        expected_result = "Provided API object has unsupported 'emit()' method. Its parameters do not correspond to the required!" \
                "Expected parameters are: 'message_type: str', 'message_subtype: str', 'message: str'"
        # cleanup
        API._instance = None
        with pytest.raises(AttributeError) as excinfo:
            API(BadAPI())
        assert expected_result in str(excinfo.value)

    def test_20_correct_api_object(self):
        # Test #20. Try to create an instance of the API class, with expected api object
        # Expected result: an instance is created
        class GoodAPI:
            def emit(self, message_type: str, message_subtype: str, message: str):
                pass
        API._instance = None
        test_api = API(GoodAPI())
        assert isinstance(test_api, API)
