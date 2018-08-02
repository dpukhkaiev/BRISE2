import os
import json

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, send, emit, join_room, leave_room, Namespace
from flask_cors import CORS
import time

from api.tasks_manager.workflow import Workflow, Task
from api.tasks_manager.model import t_parser, t_parser_2
from api.worker_manager.recruit import Recruit 

# Logging
import logging
logging.getLogger('flask.app').setLevel(logging.DEBUG)

def create_app(script_info=None):

    class MainNodeNamespace(Namespace):
        def on_ping(self, *params):
            print("\tReceived ping from main node. Arguments:", params)
            self.emit("reporting_workers", hr.workers)
            # return "pong", params

        def on_add_tasks(self, *payload):
            if len(payload) > 0:
                print('Received new tasks: %s' % len(payload[0]))
                try:
                    id_list, task_list = t_parser(payload[0])

                    for item in task_list:
                        hr.new_task(item)
                    socketio.emit('stack', flow.get_stack(), room='/front-end', namespace='/front-end')
                    self.emit('task_accepted', id_list)

                except Exception as e:
                    logging.error("ERROR '%s' in parsing received task, nothing will be added to task stack. " % e)
                    logging.error("Received task: " % payload[0])
                    self.emit("wrong_task_structure", payload[0])

    # instantiate the app
    app = Flask(__name__)
    CORS(app) # !!!     

    # WebSocket
    app.config['SECRET_KEY'] = 'secret!'
    socketio = SocketIO(app, logger=True, engineio_logger=True)
    socketio.on_namespace(MainNodeNamespace("/main_node"))

    # workflow instance with tasks stack
    flow = Workflow()

    # worker manager/explorer
    hr = Recruit(flow, socketio)
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

    @app.route('/ping', methods=['GET'])
    def ping():
        return jsonify({
            'status': 'success',
            'message': 'pong!'
        }), 200

    @app.route('/stack', methods=['GET'])
    def get_stack():
        '''
        Get current task stack
        '''
        response_object = {
            'status': 'fail',
            'message': 'No answer'
        }
        try:
            stack = flow.get_stack()
            if not stack:
                response_object['message'] = 'empty'
                return jsonify(response_object), 200
            else:
                response_object = {
                    'status': 'success',
                    'data': stack
                }
                return jsonify(response_object), 200
        except ValueError:
            return jsonify(response_object), 404

    @app.route('/task/add', methods=['POST'])
    def add_tasks():
        ''' Get new tasks from JSON
            Mimetype - application/json
        '''
        # request data
        post_data = request.get_json()

        response_object = {
            # default response
            'status': 'fail',
            'message': 'invalid payload.'
        }

        if not post_data:
            return jsonify(response_object), 400

        # try:
        # parse data in to task list
        if 'request_type' in post_data and post_data['request_type'] == 'send_task':
            id_list, task_list = t_parser_2(post_data)
        else:
            id_list, task_list = t_parser(post_data)


        print(" New tasks:", len(task_list))

        if bool(task_list):
            for item in task_list:
                hr.new_task(item)

            # upd stack obj on the client's side
            socketio.emit('stack', flow.get_stack(), room='/front-end', namespace='/front-end')

            response_object['status'] = 'success'
            response_object['response_type'] = 'send_task'
            response_object['id'] = id_list
            response_object['message'] = f'{len(task_list)} task(s) are accepted!'
            return jsonify(response_object), 201
        else:
            response_object['message'] = 'Sorry. That task can not run.'
            return jsonify(response_object), 400
        # except:
        #     return jsonify(response_object), 400

    @app.route('/result/format', methods=['PUT'])
    def get_via_format():
        """ Reply with special fields
            Mimetype - application/json
        """
        # request data
        post_data = request.get_json()
        # default response
        response_object = {
            'status': 'fail',
            'message': 'invalid payload.'
        }

        if not post_data:
            return jsonify(response_object), 400

        structure = hr.results_struct(post_data)
        return jsonify(structure), 200

    @app.route('/result/<task_id>', methods=['GET'])
    def get_single_node(task_id):
        """Get single result"""
        response_object = {
            'status': 'fail',
            'message': 'task does not exist'
        }
        result = hr.results(task_id)
        if not result:
            return jsonify(response_object), 404
        else:
            response_object = {
                'time': time.time(),
                'result': result
            }
            return jsonify(response_object), 200

    # ---------------------------- Events ------------
    #

    # managing array with curent workers
    @socketio.on('connect', namespace='/status')
    def connected():
        hr.workers.append(request.sid)

    @socketio.on('disconnect', namespace='/status')
    def disconnect():
        hr.workers.remove(request.sid)

    # --------------------------------------------
    # managing array with curent Front-end clients
    @socketio.on('join', namespace='/front-end')
    def on_join(data):
        room = data['room']
        print("SERVER connection. Room", data)
        join_room(room)
        front_clients.append(request.sid)

    @socketio.on('leave', namespace='/front-end')
    def on_leave(data):
        room = data['room']
        leave_room(room)
        front_clients.remove(request.sid)

    # BUG There is a problem when the server gets up later than the clientt
    @socketio.on('disconnect', namespace='/front-end')
    def front_disconnect():
        if request.sid in front_clients:
            front_clients.remove(request.sid)
    # --------------------------------------------

    @socketio.on('ping')
    def ping_pong(json):
        print(' Ping from: ' + str(request.sid))
        return 'server: pong!'

    #-- Task workflow
    # Checking if worker confirm a task
    @socketio.on('assign', namespace='/task')
    def task_confirm(*argv):
        hr.task_confirm(argv[0])
        # upd stack obj on the client's side
        socketio.emit('stack', flow.get_stack(), room='/front-end', namespace='/front-end')

    # Listen to the results from the worker
    @socketio.on('result', namespace='/task')
    def handle_result(json):
        temp_id = hr.analysis_res(json)
        if temp_id is not None:
            socketio.emit('get_results', json, namespace='/main_node')
            socketio.emit('result', hr.result[temp_id], room='/front-end', namespace='/front-end')

    @socketio.on('all result', namespace='/front-end')
    def all_result():
        emit('all result',
        json.dumps({'res': list(hr.result.values()), 'stack': hr.flow.get_stack()}),
        namespace='/front-end')

    return socketio, app

