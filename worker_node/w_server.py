
import os
import threading

from flask import Flask, request, jsonify, redirect, url_for
from concurrent.futures import ThreadPoolExecutor


# DOCS https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor
executor = ThreadPoolExecutor(1)
# promisse for worker execution. Has the last executed stream
prm = None
task_id = None

# Flask init
w_app = Flask(__name__)

from worker import work, random_1, random_2
# Object with available executable methods
menu = {
    'random_1': random_1,
    'random_2': random_2,
    'work': work
}

# START router config
@w_app.route('/', methods=['GET', 'POST'])
def index():
    ''' Ping request. Get results
    '''
    return jsonify({
        'status': 'online',
        'message': 'pong!',
        'node': os.environ['workername'],
        'result': prm.result(0) if prm and hasattr(prm, 'result') and prm.done() else 'null',
        'id': task_id or 'null'
    }), 200

@w_app.route('/run', methods=['POST'])
def run():
    ''' POST new task
        Mimetype: application/json
    '''
    response_object = {
        'status': 'fail',
        'message': 'No status'
    }
    try:
        global prm
        global task_id
        
        new_task = request.get_json()
        if not new_task:
            # empty request
            return jsonify(response_object), 404
        elif prm and not prm.done(): 
            # if worker busy
            return redirect(url_for('get_status'))
        else:
            if not new_task['run']['method'] in menu:
                # if worker don't have method 
                response_object = {
                    'status': 'fail',
                    'message': 'wrong method'
                }
                return jsonify(response_object), 404
            task_id = new_task['id']
            # pointer to method execution
            method = menu[new_task['run']['method']]
            # Thread
            prm = executor.submit(method, new_task['run']['param'])

            response_object = {
                'status': 'run',
                'node': os.environ['workername'],
                'method': new_task['run']['method'],
                'id': new_task['id']
            }
            return jsonify(response_object), 200
    except ValueError:
        return jsonify(response_object), 404

@w_app.route('/status', methods=['GET'])
def get_status():
    ''' Worker status. Check thread
    '''
    response_object = {
        'status': 'fail',
        'message': 'no status'
    }
    try:
        if prm:
            # check thread status            
            done = prm.done()
            response_object = {
                'status': 'free' if done else 'working',
                'message': 'done' if done else 'in progress..',
                'free': done 
            }
            return jsonify(response_object), 404
        else:
            response_object = {
                'status': 'free',
                'message': 'ready'
            }
            return jsonify(response_object), 200
    except ValueError:
        return jsonify(response_object), 404

@w_app.route('/terminate/<req_id>', methods=['DELETE'])
def term_single_task(req_id):
    ''' Terminate single task. Get task Id 
    '''
    global task_id
    response_object = {
        'status': 'ok',
        'message': 'delete'
    }

    if task_id is req_id:
        return prm.shutdown()
    else:
        response_object = {
            'status': 'wrong ID',
            'temp id': task_id,
            'request id': req_id
        }
        return jsonify(response_object), 200


# end router config


def readConfig(fileName='config.json'):
    try:
        with open(fileName, 'r') as cfile:
            config = json.loads(cfile.read())
            return config

    except IOError as e:
        print('No config file found!')
        print(e)
        return {}
    except ValueError as e:
        print('Invalid config file!')
        print(e)
        return {}

if __name__ == "__main__": 
    w_app.run(debug=True,host='0.0.0.0',port=8080)
    # run()