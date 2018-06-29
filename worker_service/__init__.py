import os


from flask import Flask, jsonify, request
from flask_socketio import SocketIO, send, emit
from flask_cors import CORS
import time

from api.tasks_manager.workflow import Workflow, Task
from api.tasks_manager.model import t_parser, t_parser_2
from api.worker_manager.recruit import Recruit 

# Logging
import logging


# workflow instance with tasks stack
flow = Workflow()

def create_app(script_info=None):
    # instantiate the app
    app = Flask(__name__)
    CORS(app) # !!!     

    # WebSocket
    app.config['SECRET_KEY'] = 'secret!'
    socketio = SocketIO(app, logger=True, engineio_logger=True)
    logging.getLogger('socketio').setLevel(logging.DEBUG)
    
    # ---------------------------------------- HTTP
    @app.route('/')
    def index():
        return jsonify({'index': 'Please stand by!', 
        'workers': str(hr.workers), 
        "results": hr.result,
        'stack': hr.flow.get_stack()
        }),200

    @app.route('/worker')
    def w_id():
        return jsonify({'name': 'special worker', 
        'workers': str(hr.workers), 
        "results": hr.result,
        'ping': hr.test()
        }),200

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

        try:
            # parse data in to task list
            if 'request_type' in post_data and post_data['request_type'] == 'send_task': 
                id_list, task_list = t_parser_2(post_data) 
            else: 
                id_list, task_list = t_parser(post_data)
                

            print(" New tasks:", len(task_list))     
            
            if bool(task_list):
                for item in task_list:
                    flow.add_task(item)

                response_object['status'] = 'success'
                response_object['response_type'] = 'send_task'
                response_object['id'] = id_list
                response_object['message'] = f'{len(task_list)} task(s) are accepted!'
                return jsonify(response_object), 201
            else:
                response_object['message'] = 'Sorry. That task can not run.'
                return jsonify(response_object), 400
        except:
            return jsonify(response_object), 400

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

    # ---------------------------- Events ------------ 
    # 

    # managing array with curent workers
    @socketio.on('connect', namespace='/status')
    def connected():
        hr.workers.append(request.sid)
        print('server.connected :: ', request.sid)     

    @socketio.on('disconnect', namespace='/status')
    def disconnect():
        hr.workers.remove(request.sid)
        print('server.disconnect :: ', request.sid)     

    @socketio.on('ping')
    def ping_pong(json):
        print(' Ping from: ' + str(request.sid))
        return 'server: pong!'

    # Task workflow
    @socketio.on('assign', namespace='/task')
    def task_confirm(*argv):
        hr.task_confirm(argv[0])

    @socketio.on('result', namespace='/task')
    def handle_result(json):
        hr.analysis_res(json)

    # worker manager/explorer
    hr = Recruit(flow, socketio)
    hr.status()

    return socketio, app

