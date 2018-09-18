import os
import threading # ?
import logging
from concurrent.futures import ThreadPoolExecutor

from socketIO_client import SocketIO, BaseNamespace # GitHub - https://github.com/invisibleroads/socketIO-client
from worker import work, random_1, random_2, energy_consumption, taskNB # available workers methods

logging.getLogger('socketIO-client').setLevel(logging.DEBUG)
logging.basicConfig()

executor = ThreadPoolExecutor(1) # DOCS https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor

# promisse for worker execution. Has the last executed stream
prm = None
task_id = None
task_iterator = 0

# Object with available executable methods
menu = {
    'random_1': random_1,
    'random_2': random_2,
    'energy_consumption': energy_consumption,
    'taskNB': taskNB,
    'work': work
}

# -----------------------------------------------
# Namespace
# -----------------------------------------------

class StatusNamespace(BaseNamespace):
    def on_pong_status_response(self, *args):
        print(':: status pong', args)

class TaskNamespace(BaseNamespace):
    def on_pong_task_response(self, *args):
        print(':: task pong', args)
# -----------------------------------------------
# Connect to worker service
socketIO = SocketIO('w_service', 80, BaseNamespace)
 
status = socketIO.define(StatusNamespace, '/status')
task = socketIO.define(TaskNamespace, '/task')

# -----------------------------------------------
# Basic functionality

def ping_obj(*argv):
    ''' Ping response'''
    return {
        'message': 'pong!',
        'node': os.environ['workername'],
        'status': 'done' if prm and hasattr(prm, 'result') and prm.done() else 'null',
        'task id': task_id or 'null'
    }

def run_task(*argv):
    ''' Run new task '''
    response_object = {
        'status': 'fail',
        'message': 'null'
    }
    global prm
    global task_id
    global task_iterator

    # separate new task
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
            prm = executor.submit(method, new_task['run']['param'])
            prm.add_done_callback(lambda ftr: task.emit('result', task_result(ftr.result())))

            response_object = {
                'status': 'run',
                'node': os.environ['workername'],
                'method': new_task['run']['method'],
                'task id': new_task['id']
            }

    task.emit('assign', response_object)

def worker_status():
    ''' Worker status. Check thread '''
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

def term_task(req_id):
    ''' Terminate task '''
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

def task_result(data):
    ''' Get results '''
    return {
        'worker status': 'online',
        'node': os.environ['workername'],
        'result': prm.result(0) if prm and hasattr(prm, 'result') and prm.done() else str(data),
        'task id': task_id or 'null'
    }


# ------------------------------------------
# Listen events

status.on('ping', ping_obj)

task.on('assign', run_task)
task.on('status', worker_status)
task.on('terminate', term_task)
task.on('result', task_result)

# Registration. Hello!
socketIO.emit('ping', {'worker': os.getenv('workername')})

socketIO.wait()