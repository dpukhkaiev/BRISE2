from socketIO_client import SocketIO, BaseNamespace
import time
# import logging
# logging.getLogger("socketIO-client").setLevel(logging.DEBUG)
# logging.basicConfig()



class WSClient(SocketIO):

    def __init__(self, wsclient):
        # Creating the SocketIO object and connecting to main node namespace - "/main_node"
        super().__init__(wsclient)
        self.ws_namespace = self.define(BaseNamespace, "/main_node")

        # Defining events that will be processed by the Worker Service Client.
        self.ws_namespace.on("connect", self.__reconnect)
        self.ws_namespace.on("ping_response", self.__ping_response)
        self.ws_namespace.on("task_accepted", self.__task_accepted)
        self.ws_namespace.on("wrong_task_structure", self.__wrong_task_structure)
        self.ws_namespace.on("task_results", self.__task_results)

        # Verifying connection by sending "ping" event to Worker Service into main node namespace.
        # Waiting for response, if response is OK - proceed.
        self.connection_ok = False
        while not self.connection_ok:
            self.ws_namespace.emit('ping')
            self.wait(0.1)

        # Properties that holds current task data.
        self.ids = []

    ####################################################################################################################
    # Private methods that are reacting to the events FROM Worker Service Described below.
    # They cannot be accessed from outside of the class and manipulates task data stored inside object.
    #
    def __reconnect(self):
        print("Worker Service has been connected!")

    def __ping_response(self, *args):
        print("Worker Service have {0} connected workers: {1}".format(len(args[0]), str(args[0])))
        self.connection_ok = True

    def __task_accepted(self, ids):
        self.ids = ids

    def __wrong_task_structure(self, received_task):
        self.ws_namespace.disconnect()
        self.disconnect()
        raise TypeError("Incorrect task structure:\n%s" % received_task)

    def __task_results(self, results):
        print(results)


    def __perform_cleanup(self):
        self.ids = []

    ####################################################################################################################
    # Public methods accessible outside of the class.
    def send_task(self, task, timeout):
        self.__perform_cleanup()
        self.ws_namespace.emit('add_tasks', task) # responce - task_accepted or wrong_task_structure
        self.wait(timeout)
        print('finished task')

if __name__ == "__main__":
    wsclient = 'w_service:80'
    task_data = [
        {"task_name": "random_1",
                    "params": {
                        "threads": "1",
                        "frequency": "2901.0"},
                    "worker_config": {"ws_file": "Radix-1000mio_avg.csv"}
         },
        {"task_name": "random_2",
                    "params": {
                        "threads": "4",
                        "frequency": "1900.0"},
                    "worker_config": {"ws_file": "Radix-1000mio_avg.csv"}
         }
    ]
    client = WSClient(wsclient)
    client.send_task(task_data, 1)
