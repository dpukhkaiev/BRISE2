# worker_service/api/router.py

from flask import Blueprint, jsonify, request
from .tasks_manager.workflow import Workflow, Task
from .tasks_manager.model import t_parser, t_parser_2
from .worker_manager.recruit import Recruit 

import time


# initialization flask router blueprint
service_blueprint = Blueprint('service', __name__, static_folder='static')

# workflow instance with tasks stack
flow = Workflow()

# worker manager/discover
hr = Recruit(flow)
hr.status()


@service_blueprint.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = "name-1"
        email = "mainl2"
    else:
        username = "default"
        email = "default" 
    return jsonify({'1': username, '2': email}), 200

@service_blueprint.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify({
        'status': 'success',
        'message': 'pong!'
    }), 200


@service_blueprint.route('/result/format', methods=['PUT'])
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


@service_blueprint.route('/result/all', methods=['GET'])
def get_all_nodes():
    """ Get all result
    """
    response_object = {
        'time': time.time(),
        'results': hr.results()
    }
    return jsonify(response_object), 200


@service_blueprint.route('/result/<task_id>', methods=['GET'])
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


@service_blueprint.route('/task/add', methods=['POST'])
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

@service_blueprint.route('/stack', methods=['GET'])
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

