import os
import threading # ?
import logging
import socketio
from concurrent.futures import ThreadPoolExecutor
import logging

from worker_tools.reflective_worker_method_import import generate_menu

logging.getLogger('socketIO-client').setLevel(logging.INFO)
logging.basicConfig()

executor = ThreadPoolExecutor(1) # DOCS https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor

# promise for worker execution. Has the last executed stream
prm = None
task_id = None
task_iterator = 0

# Generate object with available executable methods
menu = generate_menu()

# Connect to worker service
socketIO = socketio.Client()


# -----------------------------------------------
# Basic functionality
@socketIO.on('ping')
def ping_obj(*argv):
    """ Ping response """
    return {
        'message': 'pong!',
        'node': os.environ['workername'],
        'status': 'done' if prm and hasattr(prm, 'result') and prm.done() else 'null',
        'task id': task_id or 'null'
    }

@socketIO.on('reg_response', namespace='/worker_management')
def reg_response(sid, data):
    logging.getLogger(__name__).info("Server confirmed registration")

@socketIO.on('assign', namespace='/worker_management')
def run_task(*argv):
    """ Run new task """
    response_object = {
        'status': 'fail',
        'message': 'null'
    }
    global prm
    global task_id
    global task_iterator

    # separate new task
    new_task = None
    if argv:
        new_task = argv[0]

    if not new_task:
        # empty request 
        response_object['message'] = 'no task'
    elif prm and not prm.done(): 
        # if worker busy
        response_object['message']='busy'
    else:
        if not new_task['run']['method'] in menu:
            # if worker don't have method 
            response_object['message']='wrong method'
        else:
            task_id = new_task['id']
            # pointer to method execution
            method = menu[new_task['run']['method']]

            # thread
            task_iterator=+1
            prm = executor.submit(method, new_task['run']['param'],new_task['scenario'])
            prm.add_done_callback(lambda ftr: socketIO.emit('result', task_result(ftr.result()), namespace='/worker_management'))

            response_object = {
                'status': 'run',
                'node': os.environ['workername'],
                'method': new_task['run']['method'],
                'task id': new_task['id']
            }

    socketIO.emit('assign', response_object, namespace='/worker_management')

@socketIO.on('status', namespace='/worker_management')
def worker_status():
    """ Worker status. Check thread """
    if prm:            
        done = prm.done()
        response_object = {
            'status': 'free' if done else 'working',
            'message': 'done' if done else 'in progress..'
        }
        return response_object
    else:
        response_object = {
            'status': 'free',
            'message': 'worker ready'
        }
        return response_object

@socketIO.on('terminate', namespace='/worker_management')
def term_task(req_id):
    """ Terminate task """
    global task_id
    response_object = {
        'status': 'wrong id',
        'request id': req_id
    }
    if task_id is req_id:
        response_object.status = prm.shutdown()
        return response_object
    else:
        return response_object

@socketIO.on('result', namespace='/worker_management')
def task_result(data):
    """ Get results
            The same structure will be send to main-node
    """
    return {
        'worker': os.environ['workername'],
        'result': prm.result(0) if prm and hasattr(prm, 'result') and prm.done() else str(data),
        'task id': task_id or 'null'
    }

@socketIO.on('connect')
def on_connect():
    logging.getLogger(__name__).info("Connected to server. Sending registration data...")
    socketIO.emit('register_worker', namespace='/worker_management', callback=print)

socketIO.connect('http://w_service:49153', namespaces=['/worker_management'])
socketIO.wait()