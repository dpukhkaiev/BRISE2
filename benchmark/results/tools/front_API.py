from logging import getLogger
from tools.singleton import Singleton


class API(metaclass=Singleton):
    """
            The singleton - enabled decorator for the API object with exposed `send` method instead emit.
    """
    # These should be kept updated according to the APIMessageBuilder functionality!
    SUPPORTED_MESSAGES = {
        "LOG": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        "DEFAULT": ["CONFIGURATION"],
        "NEW": ["CONFIGURATION", "TASK"],
        "PREDICTIONS": ["CONFIGURATIONS"],
        "FINAL": ["CONFIGURATION"],
        "EXPERIMENT": ["DESCRIPTION"]
    }

    def __init__(self, api_object=None):
        """
            Initializes API singleton (with or without provided API object to wrap).

        :param api_object: Object. Should support method "emit" with following signature:
                api_object.emit(string_event_type, jsonable_payload)
        """

        self.logger = getLogger(__name__)

        if not api_object:
            self.logger.warning("Running BRISE without the API!")

            class DummyAPI:
                """Stub for the api object"""

                def emit(self, *args, **kwargs): pass

            self._api_object = DummyAPI()
        else:
            self._api_object = api_object

    def send(self, message_type: str, message_subtype: str, **key_value_params):
        """
            Actual wrapper for the "emit" method of the API object.
        :param message_type: String. One of the supported types: SUPPORTED_MESSAGES.keys()
        :param message_subtype: String. Subtype of message with respect to the message type: SUPPORTED_MESSAGES[TYPE]
        :param key_value_params: Parameters that will be passed to the message constructor in APIMessageBuilder class.
        :return: Result of API`s emit action.
        """

        try:
            assert type(message_type) == str, \
                "Wrong API message type object! Got: %s, should be string." % type(message_type)

            assert type(message_subtype) == str, \
                "Wrong API message subtype object! Got: %s, should be string." % type(message_subtype)

            assert message_type.upper() in API.SUPPORTED_MESSAGES.keys(), \
                "Message type is not supported! Got: %s, supported: %s" % \
                (message_type, str(list(API.SUPPORTED_MESSAGES.keys())))

            assert message_subtype.upper() in API.SUPPORTED_MESSAGES[message_type.upper()], \
                "Message subtype is not supported! Got %s, supported: %s" % \
                (message_subtype.upper(), str(API.SUPPORTED_MESSAGES[message_type.upper()]))

            # All is OK, sending the message.
            # --lowercase
            return self._api_object.emit(message_type.lower(),
                                         message_subtype.lower(),
                                         APIMessageBuilder.build(message_type.upper(), **key_value_params))

        except AssertionError as error:
            self.logger.error(error)


class APIMessageBuilder:
    """
        This enumeration class is responsible for the construction of payload of each message type.
        Each enumeration in these class in actual builder function.

        Currently supported message *types* are:
            LOG - payload is a string.
            NEW, DEFAULT, PREDICTIONS, FINAL - payload is a list of dictionaries with mandatory fields "
                configurations" and "results" and additional fields (for the extension).
            EXPERIMENT - payload is a dictionary.

        Usage (used only in the API class):
        APIMessageBuilder.LOG(msg="log message")
        APIMessageBuilder.TASK(configurations=[[1,2,3], .. [3,2,1]], results=[[2,3], .. [5,4]], field=[[..], .. [..]])
        APIMessageBuilder.EXPERIMENT(global_config={..}, experiment_config={..})
    """

    @staticmethod
    def build(message_type: str, **kwargs):
        """
            Call the appropriate message constructor and return built message.
        :param message_type: String.
        :param kwargs: data to form a payload.
        :return: Message payload (string for LOG, list for TASK, dict for EXPERIMENT).
        """
        return {
            "LOG": APIMessageBuilder._build_log_message,
            "NEW": APIMessageBuilder._build_task_message,
            "PREDICTIONS": APIMessageBuilder._build_task_message,
            "DEFAULT": APIMessageBuilder._build_task_message,
            "FINAL": APIMessageBuilder._build_task_message,
            "EXPERIMENT": APIMessageBuilder._build_experiment_message
        }[message_type.upper()](**kwargs)

    @staticmethod
    def _build_log_message(**kwargs) -> str:
        """
            Takes all values from key parameters and formats one message
        :param kwargs: parameters specified for formatting message. Usually should be {'msg': string_message}
        :return: String - message.
        """
        return "".join(str(x) for x in kwargs.values())

    @staticmethod
    def _build_task_message(**kwargs) -> list:
        """
            Builds list of dictionaries each representing the task (configuration, result and other metadata).

        :param kwargs: Should contain at least "configuration" and "result" key parameters, values - list of lists.

            Example of shape if only "configurations" and "results" have been provided (other key params also possible):
            {
                "configurations" : [[2900.0, 12], [1600.0, 2]],
                "results" : [[100], [500]]
            }

        :return: List of dictionaries with specified keys.
        """
        # Validation of input.
        try:
            # Verify that all mandatory fields provided.
            assert "configurations" in kwargs.keys(), "The configurations(key parameter) are not provided!"
            assert "results" in kwargs.keys(), "The results(key parameter) are not provided!"

            # Verify that length of all parameters are the same.
            assert all(len(kwargs[key]) == len(kwargs["configurations"]) for key in kwargs.keys()), \
                "Different sizes of provided parameters!\n%s" % str(kwargs)
        except AssertionError as error:
            getLogger(__name__).error(error)
            raise KeyError("Invalid parameters passed to send message via API: %s" % error)

        message = []

        for index in range(len(kwargs["configurations"])):
            one_task = {}
            for field in list(kwargs.keys()):
                one_task[field] = kwargs[field][index]
            message.append(one_task)

        return message

    @staticmethod
    def _build_experiment_message(**kwargs) -> dict:
        """
            Takes all key-value parameters and checks if "global_config" and "experiment_description" presents.
            Currently it just provides validation of input (needed fields are present).

            !!! In future, if new subtypes of the"EXPERIMENT" type will appear - this method should be refined.

        :param kwargs: "global_config" and "experiment_config" as mandatory fields.
        :return: Dictionary.
        """
        # Validation
        try:
            assert "global_config" in kwargs.keys(), "The global configuration is not provided!"
            assert "experiment_description" in kwargs.keys(), "The experiment description is not provided!"
        except AssertionError as error:
            getLogger(__name__).error(error)

        return {
            "global configuration": kwargs["global_config"],
            "experiment description": kwargs["experiment_description"],
            "searchspace_description": kwargs["searchspace_description"]
        }
