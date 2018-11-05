from logging import getLogger


class Singleton(type):
    """
            Meta class. Ensures that instances of it (regular class) has only one instance
        (using _instance field of class).
            These metaclass could be reused in future, but currently only API uses it.
            https://sourcemaking.com/design_patterns/singleton
            https://sourcemaking.com/design_patterns/singleton/python/1
    """

    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class API(metaclass=Singleton):
    """
        The singleton - enabled decorator for the API object.

        TODO: Finish description of the class.
    """

    # These should be kept updated according to the APIMessageBuilder functionality!
    SUPPORTED_MESSAGES = {
        "LOG": ["debug", "info", "warning", "error", "critical"],
        "TASK": ["default", "new", "predictions", "final"],
        "EXPERIMENT": ["configuration"]
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
                def emit(self): pass
            self._api_object = DummyAPI()
        else:
            self._api_object = api_object

    def send(self, message_type: str, message_subtype: str, **key_value_params):
        """
            Actual wrapper for the "emit" method of the API object.
        :param message_type: String. One of the supported types: "LOG", "TASK", "EXPERIMENT"
        :param message_subtype: String. Subtype of message with respect to the message type.
        :param key_value_params: Parameters that will be passed to the message constructor in APIMessageBuilder class.
        :return: None
        """

        try:
            assert message_type == str, "API message type! Got: %s, should be string." % message_type
            assert message_subtype == str, "API message type! Got: %s, should be string." % message_subtype
            assert message_type.upper() in API.SUPPORTED_MESSAGES.keys(), "Message type is not supported!"
            assert message_subtype.upper() in API.SUPPORTED_MESSAGES[message_type], "Message type is not supported!"
        except AssertionError as err:
            self.logger.error(err)

        self._api_object.emit(message_type.upper(),
                              {message_subtype.upper(), APIMessageBuilder.build(message_type, **key_value_params)}
                              )


class APIMessageBuilder:
    """
        This enumeration class is responsible for the construction of payload of each message type.
        Each enumeration in these class in actual builder function.

        Currently supported message *types* are:
            LOG - payload is a string.
            TASK - payload is a list of dictionaries with mandatory fields "configuration" and "result" and
                    additional fields (for the extension).
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
        :param message_type:
        :param kwargs:
        :return: Message payload (string for LOG, list for TASK, dict for EXPERIMENT).
        """
        return {
            "LOG": APIMessageBuilder._build_log_message,
            "TASK": APIMessageBuilder._build_task_message,
            "EXPERIMENT": APIMessageBuilder._build_task_message
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
            Builds list of dictionaries each representing the task (configuration and result).

        :param kwargs: Should contain at least "configuration" and "result" key parameters, values - list of lists.

            Example of shape, if only "configurations" and "results" have been provided (other key params also possible):
            {
                "configurations" : [[2900.0, 12], [1600.0, 2]],
                "results" : [[100], [500]]
            }

        :return: List of dictionaries with specified keys.
        """
        # Validation of input.
        try:
            assert "configurations" in kwargs.keys(), "The configurations(key parameter) are not provided!"
            assert "results" in kwargs.keys(), "The results(key parameter) are not provided!"

            assert all(len(kwargs[key]) == len(kwargs["configurations"]) for key in kwargs.keys()), \
                "Different sizes of provided parameters!\n%s" % str(kwargs)
        except AssertionError as err:
            getLogger(__name__).error(err)

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
            Takes all key-value parameters and checks if "global_config" and "experiment_config" presents.
            Currently it just provides validation of input (needed fields are present).
            TODO: In future, if new subtypes of the"EXPERIMENT" type will appear - this method should be refined.
        :param kwargs: "global_config" and "experiment_config" as mandatory fields.
        :return: Dictionary with same
        """
        # Validation
        try:
            assert "global_config" in kwargs.keys(), "The global configuration is not provided!"
            assert "experiment_config" in kwargs.keys(), "The experiment configuration is not provided!"
        except AssertionError as err:
            getLogger(__name__).error(err)

        return {
            "global configuration": kwargs["global_config"],
            "experiment configuration": kwargs["experiment_config"]
        }
