import json

from flask import Flask, jsonify
import socketio

from api.tasks_manager.workflow import Workflow, Task
from api.tasks_manager.model import task_parser
from api.worker_manager.recruit import Recruit 

# Logging
import logging
logging.getLogger('flask.app').setLevel(logging.INFO)

def create_app(script_info=None):
    socketIO = socketio.Server(logger=True, engineio_logger=False)
    # instantiate the app
    app = Flask(__name__) 
    app.wsgi_app = socketio.WSGIApp(socketIO, app.wsgi_app)
    # WebSocket
    app.config['SECRET_KEY'] = 'secret!'

    # workflow instance with tasks stack
    flow = Workflow()

    # worker manager/explorer
    hr = Recruit(flow, socketIO)
    hr.status()

    # Front-end clients
    front_clients = []
    
    # ---------------------------------------- HTTP
    @app.route('/')
    def index():
        return jsonify({'index': 'Please stand by!',
        'workers': str(hr.workers),
        "results": hr.result,
        'stack': hr.flow.get_stack(),
        'front-end': front_clients
        }),200

    # -------------------------------------- EVENTS 
    #

    #------------- Main-node events ------------------
    #

    @socketIO.on('ping', namespace='/main_node')
    def main_ping(self, *params):
            print("\tReceived ping from main node. Arguments:", params)
            socketIO.emit("ping_response", hr.workers, namespace='/main_node')

    @socketIO.on('add_tasks', namespace='/main_node')
    def add_tasks_event(self, tasks):
        if len(tasks) > 0:
            print('Received new tasks: %s' % len(tasks))
            try:
                id_list, task_list = task_parser(tasks)
                for item in task_list:
                    hr.new_task(item)
                socketIO.emit('task_accepted', id_list, namespace='/main_node')
            except Exception as error:
                logging.error("ERROR '%s' in parsing received task, nothing will be added to task stack. " % error)
                logging.error("Received task: " % tasks)
                socketIO.emit("wrong_task_structure", tasks, namespace='/main_node')

    @socketIO.on('terminate_tasks', namespace='/main_node')
    def terminate_tasks_event(self, ids):
        print("Terminating tasks: %s" % str(ids))
        for task_id in ids:
            socketIO.emit("terminate", task_id, namespace="/worker_management")

    #------------- Workers management events ------------------
    #

    # Checking if worker confirm a task
    @socketIO.on('assign', namespace='/worker_management')
    def task_confirm(sid, data):
        hr.task_confirm(data)

    # Listen to the results from the worker
    @socketIO.on('result', namespace='/worker_management')
    def handle_result(sid, json):
        temp_id = hr.analysis_res(json)
        if temp_id is not None:
            socketIO.emit('task_results', json, namespace='/main_node')

    @socketIO.on('register_worker', namespace='/worker_management')
    def register(sid):
        hr.workers.append(sid)
        print('Worker ' + sid + ' has been registered at Worker Service')
        socketIO.emit('reg_response', namespace='/worker_management', room=sid)
        return 'Server confirmed registration'
    
    @socketIO.on('unregister_worker', namespace='/worker_management')
    def unregister(sid):
        hr.workers.remove(sid)

    # ------------ General events --------------------
    #

    # managing array with curent workers
    @socketIO.on('connect')
    def connected(sid, environ):
        print(sid + ' has been connected to Worker Service')

    @socketIO.on('disconnect')
    def disconnect(sid):
        print(sid + 'has been disconnected from Worker Service')
        if (hr.workers.__contains__(sid)):
            hr.workers.remove(sid)

    @socketIO.on('ping')
    def ping_pong(sid, data):
        print(' Ping from: ' + str(sid))
        socketIO.emit("ping")

    return socketIO, app

