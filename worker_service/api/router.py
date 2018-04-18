# worker_service/api/router.py

from flask import Blueprint, jsonify, request
from .tasks_manager.workflow import Workflow, Task
from .tasks_manager.model import t_parser
from .worker_manager.recruit import Recruit 

import time


# initialization flask router blueprint
service_blueprint = Blueprint('service', __name__, static_folder='static')

# workflow instance with tasks stack
flow = Workflow()

# worker manager/discover
hr = Recruit(flow)
# hr.print()


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
    })


@service_blueprint.route('/result', methods=['GET'])
def get_all_nodes():
    """Get all result"""
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
    '''
    Get new tasks from JSON 
    Mimetype - application/json
    '''
    # request data
    post_data = request.get_json()

    response_object = {
        'status': 'fail',
        'message': 'Invalid payload.'
    }

    if not post_data:
        return jsonify(response_object), 400

    try:
        # parse data in to task list
        task_list = t_parser(post_data)
        print(" New tasks:", len(task_list))     
        
        if bool(task_list):
            for item in task_list:
                flow.add_task(item)

            response_object['status'] = 'success'
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
            return jsonify(response_object), 404
        else:
            response_object = {
                'status': 'success',
                'data': stack
            }
            return jsonify(response_object), 200
    except ValueError:
        return jsonify(response_object), 404

@service_blueprint.route('/run', methods=['GET', 'POST'])
def run_test():
    response_object = {
        'status': 'fail',
        'data': None
    }
    try:
        if request.method == 'GET':
            r = hr.assign_test() # test execution
        else:
            r = hr.spin() # Task instance
            
        if not r:
            return jsonify(response_object), 404
        else:
            response_object = {
                'status': 'assign',
                'data': r
            }
            return jsonify(response_object), 200
    except ValueError:
        return jsonify(response_object), 404