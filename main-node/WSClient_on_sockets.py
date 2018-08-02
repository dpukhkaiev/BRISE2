from socketIO_client import SocketIO, BaseNamespace

# import logging
# logging.getLogger("socketIO-client").setLevel(logging.DEBUG)
# logging.basicConfig()

class WSClientEventHandler(BaseNamespace):
    def on_connect(self):
        print("Successfully connected to Worker Service!")

    def on_reporting_workers(self, *args):
        print("Worker Service have {0} connected workers: {1}".format(len(args[0]), str(args[0])))

    def on_wrong_task_structure(self, *args):
        print("Worker Service cannot accept task that were sent because of incorrect structure: ", str(args))

    def on_task_accepted(self, *ids):
        print("WS accepted tasks with IDs:", ids[0])

    # ----------------- Data processing events
    def on_get_results(self, *result):
        print(result)

class WSClient(object):

    def __init__(self, wsclient):
        self.ws_socket_connect = SocketIO(wsclient)
        self.conected = False
        self.ws_namespace = self.ws_socket_connect.define(WSClientEventHandler, "/main_node")
        self.ws_namespace.emit('ping')
        self.ws_socket_connect.wait(0.1)

    def send_task(self, task):
        print(self.conected)
        self.ws_namespace.emit('add_tasks', task)
        self.ws_socket_connect.wait(15)

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
    client.send_task(task_data)