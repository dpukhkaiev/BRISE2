# worker_service/api/router.py

from flask import Blueprint, jsonify, request
from .tasks_manager.workflow import Workflow, Task
from .tasks_manager.model import t_parser
from .worker_manager.recruit import Recruit 


# initialization flask router blueprint
service_blueprint = Blueprint('service', __name__, static_folder='static')

# workflow instance with tasks stack
flow = Workflow()

# worker manager/discover
hr = Recruit(flow)
hr.print()


@service_blueprint.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = "name-1"
        email = "mainl2"
    else:
        username = "default"
        email = "default" 
    return jsonify({'1': username, '2': email, 'Data': flow.go_go_baby()}), 200


@service_blueprint.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify({
        'status': 'success',
        'message': 'pong!'
    })


@service_blueprint.route('/status', methods=['GET'])
def get_all_nodes():
    """Get all nodes"""
    response_object = {
        'status': 'success',
        'data': {
            'nodes': "good"
            # 'nodes': [user.to_json() for user in User.query.all()]
        }
    }
    return jsonify(response_object), 200


@service_blueprint.route('/status/<node_id>', methods=['GET'])
def get_single_node(node_id):
    """Get single node details"""
    response_object = {
        'status': 'fail',
        'message': 'Node does not exist'
    }
    try:
        # user = User.query.filter_by(id=int(node_id)).first()
        if not user:
            return jsonify(response_object), 404
        else:
            response_object = {
                'status': 'success',
                'data': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'active': user.active
                }
            }
            return jsonify(response_object), 200
    except ValueError:
        return jsonify(response_object), 404


@service_blueprint.route('/task/add', methods=['POST'])
def add_tasks():
    '''
    Get new tasks from JSON (mimetype is application/json)
    '''
    post_data = request.get_json()
    # print("POST data ::", request.form)
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
            r = hr.assign() # Task instance
            
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