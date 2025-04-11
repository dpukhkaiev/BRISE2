import logging
import os
import pika
import threading


class RabbitMQConnection(threading.Thread):
    """
    The class contains commonly used tools to communicate with Event Service
    """
    def __init__(self, module):
        super(RabbitMQConnection, self).__init__()
        self.module = module
        self.logger = logging.getLogger(str(module))
        self.bind_flag = False
        self.host = os.getenv("BRISE_EVENT_SERVICE_HOST")
        self.port = int(os.getenv("BRISE_EVENT_SERVICE_AMQP_PORT"))
        self.conn_params = pika.ConnectionParameters(self.host, self.port)
        self.connection = pika.BlockingConnection(self.conn_params)
        self.channel = self.connection.channel()
        self._is_interrupted = False
        self.bind_and_consume()

    def bind_and_consume(self):
        """
        The function to define queues to listen for
        """
        pass

    def stop(self, ch=None, method=None, properties=None, body=None):
        """
        The function for thread stop
        """
        self._is_interrupted = True

    def run(self):
        """
        Point of entry to tasks results consumers functionality,
        listening of queue with task result
        """
        try:
            while not self._is_interrupted:
                self.channel.connection.process_data_events(time_limit=1)  # 1 second
        finally:
            self.logger.info(f"{self.module} is shutting down.")
            if self.connection.is_open:
                self.connection.close()


def publish(exchange: str, routing_key: str, body):
    """
    The function to publish the message to Event Service
    :param exchange: target exchange
    :param routing_key: defines experiment ID of this message
    :param body: the body of the message
    """
    host = os.getenv("BRISE_EVENT_SERVICE_HOST")
    port = int(os.getenv("BRISE_EVENT_SERVICE_AMQP_PORT"))
    conn_params = pika.ConnectionParameters(host, port)
    channel = pika.BlockingConnection(conn_params).channel()
    try:
        channel.basic_publish(exchange=exchange, routing_key=routing_key, body=body)
    except pika.exceptions.ChannelWrongStateError as err:
        if not channel.is_open:
            logging.getLogger(exchange).warning("Attempt to send a message after closing the connection")
        else:
            raise err
