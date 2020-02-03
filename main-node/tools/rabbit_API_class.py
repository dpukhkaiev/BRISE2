import threading
import json

import pika
import pika.exceptions

from tools.singleton import Singleton


class RabbitApi(metaclass=Singleton):
    """
    The singleton - is a core API object for API class.
    """

    def __init__(self, host: str, port: int):
        """
        Constructor for RabbitApi class
        :param host (str): ip or hostname of Rabbitmq service
        :param port (int):port of Rabbitmq service
        """
        self._host = host
        self._port = port
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self._host, port=self._port))
        self.sender_lock = threading.Lock()

    def emit(self, message_type: str, message_subtype: str, message: str):
        """
        Function for sending events used by API.send()
        :param message_type: String. One of the supported types: API.SUPPORTED_MESSAGES.keys()
        :param message_subtype: String. Subtype of message with respect to the message type: API.SUPPORTED_MESSAGES[TYPE]
        :param message: String. Body of the message, built by PIMessageBuilder class
        :return:
        """
        while (True):
            try:
                with self.sender_lock:
                    with self.connection.channel() as channel:
                        channel.basic_publish(exchange=f"event_{message_type}_sender",
                                              routing_key='',
                                              properties=pika.BasicProperties(
                                                  headers={'message_subtype': message_subtype}
                                              ),
                                              body=json.dumps(message))
                    break
            except (pika.exceptions.ConnectionClosedByBroker, pika.exceptions.StreamLostError):
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self._host, port=self._port))  # Recreate terminated connection
                continue
