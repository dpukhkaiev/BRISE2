import base64
import json
import os
import pickle
import time
from threading import Thread

import pika
# USER
from logger.default_logger import BRISELogConfigurator
from main import MainThread
from tools.front_API import API
from tools.rabbit_API_class import RabbitApi

logger = BRISELogConfigurator().get_logger(__name__)
# from tools.main_mock import run as main_run

# Initialize the API singleton
API(api_object=RabbitApi(os.getenv("BRISE_EVENT_SERVICE_HOST"), os.getenv("BRISE_EVENT_SERVICE_AMQP_PORT")))


class ConsumerThread(Thread):
    """
    This class runs in a separate thread and handles requests client nodes (e.g. benchmark, front-end),
    connected to the `main_start_queue`, `main_status_queue`, `main_stop_queue`, `main_download_dump_queue`,
    produces results in specified queue with specified tag, works as server part of RPC
    """

    def __init__(self, host, port, *args, **kwargs):
        super(ConsumerThread, self).__init__(*args, **kwargs)

        self._host = host
        self._port = port
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self._host, port=self._port))
        self._is_interrupted = False
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)
        self.MAIN_THREAD: MainThread = MainThread()
        self.logger = BRISELogConfigurator().get_logger(__name__)

    def main_process_status(self):
        """
        The function returns the status of the main process.
        Main Thread.State.SHUTTING_DOWN means that main process now tried to stop all internal process,
        this function has to wait for the end of this process
        :return: status of main process
        """
        result = {}
        main_thread_state = MainThread.State.IDLE

        while True:
            main_thread_state = self.MAIN_THREAD.get_state()
            if main_thread_state != MainThread.State.SHUTTING_DOWN:
                break
        if main_thread_state == MainThread.State.IDLE:
            result['MAIN_PROCESS'] = {"main process": bool(False),
                                      "status": 'none'}
        elif main_thread_state == MainThread.State.RUNNING:
            result['MAIN_PROCESS'] = {"main process": bool(True),
                                      "status": 'running'}
        return result

    def main_start(self, channel, method, properties, body):
        """
        RPC function that verifies that Main-node is not running.
        If free - creates new process and starts it.

        properties.headers['body_type']: specifies the type of body content
                                         (pickle - used for benchmark or json - used for front-end),

        For json type: body["Method"] - POST: body["Data"]: has to contain pickle of experiment setup
                                      - GET: body["Data"]: could empty, in this case, default experiment will start

        If main process is already running - just return its status. (To terminate process - use relevant method).
        """
        if properties.headers['body_type'] == 'pickle':
            self.MAIN_THREAD = MainThread(experiment_setup=pickle.loads(body))
            self.MAIN_THREAD.start()
        elif properties.headers['body_type'] == 'json':
            request = json.loads(body)
            if self.MAIN_THREAD.get_state() == MainThread.State.IDLE:
                if request["Method"] == "POST":
                    self.MAIN_THREAD = MainThread(experiment_setup=pickle.loads(request["Data"]))
                    self.MAIN_THREAD.start()
                else:
                    self.MAIN_THREAD = MainThread()
                    self.MAIN_THREAD.start()
        time.sleep(0.1)
        result = self.main_process_status()
        self.channel.basic_publish(exchange='',
                                   routing_key=properties.reply_to,
                                   properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                                   body=json.dumps(result))
        self.channel.basic_ack(delivery_tag=method.delivery_tag)

    def main_status(self, channel, method, properties, body):
        """
        RPC function that returns response that contains status of main process.
        If more processes will be added - could be modified to display relevant info.
        """
        result = self.main_process_status()
        self.channel.basic_publish(exchange='',
                                   routing_key=properties.reply_to,
                                   properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                                   body=json.dumps(result))
        self.channel.basic_ack(delivery_tag=method.delivery_tag)

    def main_stop(self, channel, method, properties, body):
        """
        RPC function that verifies if main process running and if it is - terminates it.
        After it returns status of this process (should be terminated).
        :return: main_process_status()
        """
        if self.MAIN_THREAD.get_state() == MainThread.State.RUNNING:
            msg = "Stop comand from API received."
            self.channel.basic_publish(exchange='',
                                       routing_key='stop_experiment_queue',
                                       body=msg)

        result = self.main_process_status()
        self.channel.basic_publish(exchange='',
                                   routing_key=properties.reply_to,
                                   properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                                   body=json.dumps(result))
        self.channel.basic_ack(delivery_tag=method.delivery_tag)

    def download_dump_request_queue(self, channel, method, properties, body):
        """
       RPC function that returns a base64 encoded dump of the latest experiment.
       body['format']: specifies file extension of dump

       result["status"]: contains a status of a response, "ok" or "error"
       result["body"]: contains a base64 encoded dump
       result["file_name"]: contains a file name
       """
        body = json.loads(body)
        result = {"status": None, "body": None, "file_name": None}
        dump_name = os.environ.get('EXP_DUMP_NAME')
        try:
            if dump_name == 'undefined':
                result["status"] = "missing experiment file"
                API().send("log", "error", message=result["body"])
            else:
                filename = f"{dump_name}.{body['format']}"
                with open(filename, "rb") as file:
                    result["status"] = "ok"
                    result["body"] = str(base64.b64encode(file.read()), "utf-8")
                    result["file_name"] = f"{dump_name}.{body['format']}"
        except Exception as error:
            result["status"] = 'Download dump file of the experiment: %s' % error
            API().send("log", "error", message=result["status"])
        self.channel.basic_publish(exchange='',
                                   routing_key=properties.reply_to,
                                   properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                                   body=json.dumps(result))
        self.channel.basic_ack(delivery_tag=method.delivery_tag)

    def run(self):
        """
        Point of entry to the server part of PRC,
        listening of queues with PRC requests
        """
        self.channel.basic_consume(queue='main_start_queue', auto_ack=False,
                                   on_message_callback=self.main_start)
        self.channel.basic_consume(queue='main_status_queue', auto_ack=False,
                                   on_message_callback=self.main_status)
        self.channel.basic_consume(queue='main_stop_queue', auto_ack=False,
                                   on_message_callback=self.main_stop)
        self.channel.basic_consume(queue='main_download_dump_queue', auto_ack=False,
                                   on_message_callback=self.download_dump_request_queue)

        try:
            while self.channel._consumer_infos:
                self.channel.connection.process_data_events(time_limit=1)  # 1 second
                if self._is_interrupted:
                    if self.connection.is_open:
                        self.connection.close()
                    break
        finally:
            if self.connection.is_open:
                self.connection.close()

    def stop(self):
        self._is_interrupted = True


if __name__ == '__main__':
    consumer_thread = ConsumerThread(os.getenv("BRISE_EVENT_SERVICE_HOST"), os.getenv("BRISE_EVENT_SERVICE_AMQP_PORT"))
    consumer_thread.start()
    consumer_thread.join()
