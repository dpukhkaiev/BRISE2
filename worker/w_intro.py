import ctypes
import json
import logging
import os
import threading

import pika
import pika.exceptions
from worker_tools.reflective_worker_method_import import (
    get_worker_methods_as_dict
)

logging.basicConfig()


class WorkerMainThread(threading.Thread):
    """
    This class runs main worker process in a separate thread,
    connected to the `task_queue` as a consumer and sends messages when a task starts  to `taken_task_event_queue`
    and sends a result of task via  `task_result_sender` to `task_result_queue` and `finished_task_event_queue`
    """
    def __init__(self, host, port):
        """
        :param host: ip address of rabbitmq service
        :param port: port of rabbitmq main-service
        """
        super(WorkerMainThread, self).__init__()
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host, port))

        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)  # prefetch_count is a parameter that limited number of taken task
        self.channel.basic_consume(queue='task_queue',
                                   on_message_callback=self.run_task)
        self.task_dict = {}
        # Generate object with available executable methods
        self.worker_methods = get_worker_methods_as_dict()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def get_id(self):
        """
        :return: id of the respective thread
        """
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def raise_exception(self):
        """
        The function for crashing worker thread, need for a later restart. After crash task move back to the queue
        :return:
        """
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                         ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
        self.connection.close()

    def run_task(self, ch, method, properties, body):
        task: dict = json.loads(body)
        global CURRENT_TASK_ID
        CURRENT_TASK_ID = task["task_id"]
        self.logger.info(f"Got task: {task['task_name']} ID: {task['task_id']}.")

        if 'task_name' not in task.keys():
            self.logger.error(f"No task name provided in {task}")
        else:
            if not task['task_name'] in self.worker_methods:
                # if worker don't have method
                self.logger.error(f'Task {task["task_name"]} is not supported. '
                                  f'Supported Tasks are: {list(self.worker_methods.keys())}.')
            else:
                # pointer to method execution
                w_method = self.worker_methods[task["task_name"]]
                self.channel.basic_publish(exchange='', routing_key='taken_task_event_queue', body=json.dumps(task))
                # Execute task
                try:
                    result_from_worker = w_method(task)
                    if result_from_worker is None:
                        self.logger.warning(f"{w_method} did not return any results.")
                        result_from_worker = {}
                except Exception as e:
                    self.logger.error(f"Task execution failed with: {e}", exc_info=True)
                    result_from_worker = {}
                # format a result according to result structure
                for key in task["result_structure"]:
                    if key not in result_from_worker:
                        result_from_worker[key] = None
                res = {
                    'id_measurement': task["id_measurement"],
                    'task_result': {
                        'task id': task["task_id"],
                        'worker': f"{os.uname()[1]}",
                        'result': result_from_worker
                    }
                }
                self.channel.basic_publish(exchange='task_result_sender',
                                           routing_key='',
                                           body=json.dumps(res))
                ch.basic_ack(delivery_tag=method.delivery_tag)  # acknowledge that task was finished

    def run(self):
        try:
            self.channel.start_consuming()

        except pika.exceptions.AMQPError:
            pass  # in case of termination task

        except Exception as e:
            self.logger.error(f"Worker Thread was terminated by {e}.", exc_info=True)


class WorkerTerminationThread(threading.Thread):
    """
    This class runs worker termination functionality in a separate thread,
    create a dynamic queue, bind the queue to `task_termination_sender`
    and consumes this queue and terminate worker process according to termination message
    """
    def __init__(self, host, port):
        """
        :param host: ip address of rabbitmq service
        :param port: port of rabbitmq main-service
        """
        super(WorkerTerminationThread, self).__init__()
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host, port))

        self.channel = self.connection.channel()
        # subscribe for all massages in task_termination_sender exchange
        # need for broadcast messages between all workers
        termination_reg_result = self.channel.queue_declare(queue='', exclusive=True)
        termination_queue_name = termination_reg_result.method.queue

        self.channel.queue_bind(exchange='task_termination_sender', queue=termination_queue_name)
        self.channel.basic_consume(
            queue=termination_queue_name, on_message_callback=self.terminate_task, auto_ack=True)

    def get_id(self):
        """
        :return: id of the respective thread
        """
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def raise_exception(self):
        """
        The function for crashing termination thread, need for a later restart. After crash task move back to the queue
        :return:
        """
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                         ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)

    def terminate_task(self, ch, method, properties, body):
        global CURRENT_TASK_ID
        task_id = json.loads(body.decode())
        if CURRENT_TASK_ID == task_id:
            self.connection.close()
            self.raise_exception()  # cash termination thread

    def run(self):
        while self.channel._consumer_infos:
            self.channel.connection.process_data_events(time_limit=1)  # 1 second


CURRENT_TASK_ID = ""

# Basic functionality
while True:
    w_thread = WorkerMainThread(os.getenv("BRISE_EVENT_SERVICE_HOST"), os.getenv("BRISE_EVENT_SERVICE_AMQP_PORT"))
    t_thread = WorkerTerminationThread(os.getenv("BRISE_EVENT_SERVICE_HOST"),
                                       os.getenv("BRISE_EVENT_SERVICE_AMQP_PORT"))
    try:
        w_thread.start()
        t_thread.start()
        t_thread.join()
    finally:
        # in case of termination thread was crashed or finished crash worker thread and restart
        w_thread.raise_exception()
        w_thread.join()
