import copy
import datetime
import json
import logging
import os
import threading

import pika

logging.getLogger("pika").propagate = False


class WorkerServiceThread(threading.Thread):
    """
    This class runs workers management functionality in a separate thread,
    connected to the `taken_task_event_queue` and 'finished_task_event_queue' as consumer
    and sends termination command via `task_termination_sender` to all dynamic queues that create during worker start.
    """
    def __init__(self, host, port):
        """
        :param host: ip address of rabbitmq service
        :param port: port of rabbitmq main-service
        """
        super(WorkerServiceThread, self).__init__()
        self._host = host
        self._port = port
        self.logger = logging.getLogger(__name__)
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host, port))
        self.channel = self.connection.channel()
        self.channel.basic_consume(queue='taken_task_event_queue', auto_ack=True,
                                   on_message_callback=self.task_start_func)

        self.channel.basic_consume(queue='finished_task_event_queue', auto_ack=True,
                                   on_message_callback=self.task_finished_func)

        self.task_dict = {}
        self._is_interrupted = False

    def task_checker(self):
        """
        The function that checks time to time expired time for each task and sends terminate message to stragglers
        """
        if self._is_interrupted:
            return
        threading.Timer(2.0, self.task_checker).start()
        tasks_snapshot = copy.deepcopy(self.task_dict)
        for key in tasks_snapshot.keys():
            if tasks_snapshot[key]["termination_time"] < datetime.datetime.now():
                try:
                    del (self.task_dict[key])
                    self.logger.debug("Terminating Task {id_task}.".format(id_task=key))
                    if self.connection.is_open and not self._is_interrupted:
                        with pika.BlockingConnection(
                                pika.ConnectionParameters(host=self._host, port=self._port)) as connection:
                            channel = connection.channel()
                            channel.basic_publish(exchange='task_termination_sender',
                                                  routing_key='',
                                                  body=json.dumps(key))
                except KeyError:
                    self.logger.info("Termination after finish")

    def task_start_func(self, channel, method, properties, body):
        """
        Callback for task start event
        :param channel: pika.Channel
        :param method:  pika.spec.Basic.GetOk
        :param properties: pika.spec.BasicProperties
        :param body: task description in bytes format
        """
        task_description = json.loads(body.decode())
        task_description["start_run_time"] = datetime.datetime.now()
        if task_description["time_for_run"] == float("inf"):
            task_description["termination_time"] = datetime.datetime.max
        else:
            task_description["termination_time"] = datetime.datetime.now() + datetime.timedelta(
                seconds=task_description["time_for_run"])
        self.task_dict[task_description["task_id"]] = task_description

    def task_finished_func(self, channel, method, properties, body):
        """
        Callback for task finish event
        :param channel: pika.Channel
        :param method:  pika.spec.Basic.GetOk
        :param properties: pika.spec.BasicProperties
        :param body: task description in bytes format
        """
        task_response = json.loads(body.decode())
        try:
            del (self.task_dict[task_response["task_result"]["task id"]])
        except KeyError:
            self.logger.info("The old task was received")

    def run(self):
        """
        Point of entry to tasks events consumers functionality,
        founding stragglers
        """
        self.task_checker()
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


def run():
    workers_service_thread = WorkerServiceThread(os.getenv("BRISE_EVENT_SERVICE_HOST"),
                                                 os.getenv("BRISE_EVENT_SERVICE_AMQP_PORT"))
    workers_service_thread.start()
    workers_service_thread.join()
    workers_service_thread.stop()


if __name__ == "__main__":
    run()
