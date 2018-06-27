import os
import requests

from flask_socketio import SocketIO, send, emit
import time
from random import randint
from concurrent.futures import ThreadPoolExecutor


# LOGIN
import logging
# logging.basicConfig(filename='recruit.log',level=logging.DEBUG)
logging.getLogger('socketio').setLevel(logging.DEBUG)
logging.getLogger('engineio').setLevel(logging.DEBUG)

default_logger = logging.getLogger('socketio')

class Recruit():
    '''
    Class for discovering/managing workers
    '''
     
    def __init__(self, flow, socket):
        # Set how much workers we have
        # self.workers = ['alpha', 'beta', 'gamma', 'delta'][:int(os.getenv('WORKER_COUNT'))]
        self.workers = []
        self.flow = flow
        self.result = dict()
        self._executor = ThreadPoolExecutor(1).submit(self._loop)
        self.socket = socket


        default_logger.info('TEST -- Constructor')

        # managing array with curent workers
        self.socket.on('connect', namespace='/status')
        def connected():
            # print('------ connected: ' + str(request.namespace.socket.sessid))
            default_logger.info('LOGER -- Connected')
            workers.append('request.namespace')
            return 'from server:connected'     

        self.socket.on('disconnect', namespace='/status')
        def disconnect():
            # print('------ disconnected: ' + str((request.namespace.socket.sessid)))
            default_logger.info('LOGER -- Disconnecting')
            workers.remove('request.namespace')
            return 'from server:disconnect'

        self.socket.on('ping')
        def ping_pong():
            print(' PING: ' + str((request.namespace.socket.sessid)))
            return 'server - pong :: HR'

        self.socket.on('result', namespace='/task')
        def handle_result(json):
            self.analysis_res(json)
            print(' received results: ' + str(json))

    def __del__(self):
        self._executor.cancel()

    def _loop(self):
        while True: 
            # wait task in queue
            time.sleep(1) 
            if self.flow.stack.queue:
                # if there is a task(s) in the queue
                print(" Spin:", self.spin())
                time.sleep(1)

            for task in self.flow.get_stack():
                if task["id"] not in self.result:
                    self.result[task["id"]] = task

    # def test(self):
    #     self.socket.emit('ping', {'data': 42})
    #     return 'ping'

    def status(self):
        print(" Workers:", self.workers)

    def results(self, id=False):
        if id: 
          return self.result[id] if id in self.result else None 
        else: return self.result

    def results_struct(self, struct):
        ''' Converting task structure for workers
        '''
        ''' PUT ==>
        {
            "task_name": "random_1",
            "request_type": "get_results",
            "response_struct": ["frequency", "threads", "time" ],
            "ID": [123123123, 123123124, 123123125]
        }
            <==
        {
            "task_name": "random_1",
            "response_type": "get_results",
            "params_names": ["param1", "param2", "paramN"],
            “statuses”: [status1, status2, statusN]
            "param_values": [
                [123, "value_for_param_2", 123.1],
                [112313253, "value2_for_param_2", 123123.1],
                [123, null, null]
            ]
        } '''

        answer = {
            "response_type": "get_results",
            "task_name": [],
            "param_values": [],
            "statuses": [],
            "params_names": struct["response_struct"]
        }

        for i in struct["id"]:
            if i in self.result:
                temp = self.result[i]
                answer["task_name"].append(temp["run"]["method"] if "run" in temp else "...")
                answer["statuses"].append("done" if "time" in temp["meta_data"]["result"] else "in progress")
                
                t_val = []
                for par in struct["response_struct"]:
                    if temp["meta_data"]["result"]:
                        try:
                            t_val.append(temp["meta_data"]["result"][par])
                        except:
                            with open("recruit.log", 'w') as f:
                                f.write(str(temp))
                                f.write("par:" + str(par))
                    else: t_val.append("in stack")

                answer["param_values"].append(t_val)
            else:
                answer["statuses"].append("wrong id")
                answer["task_name"].append("null")
                answer["param_values"].append(["null"])
        return answer


    def spin(self): # bind with flow.stack. Eternal loop
        ''' Pull out task from the Stack and find a worker who can complete it
        '''

        task = self.flow.pull_task()
        payload = task.to_json()
        # store task id - status
        if payload:
            self.result[payload['id']] = payload

        # success flag
        send = False  

        while task and not send:
            # TODO it is necessary to form a structure that monitors free workers
            # select random worker
            w_random = randint(0, 9)%len(self.workers)     
            
            # try assign a task to worker          
            # r = requests.post('http://'+ self.workers[w_random] +':8080/run', json=payload)
            res = None
            if workers:
                k = random.randint(0, len(workers)-1)
                print("Task send to", workers[k].socket.sessid)
                res = workers[k].emit('assign', 
                                payload, 
                                namespace='/task', 
                                callback= lambda res: task_confirm(res))

            def task_confirm(res):
                if res['status'] == 'run':
                    self.result[payload['id']]['meta_data']['accept'] = time.time()
                    self.result[payload['id']]['meta_data']['appointment'] = res['node']
                    send = True
                    task = None
                    return res

    def analysis_res(self, json_response):
        result = json_response['result']
        if result is not "null": # if worker have results
            r_id = json_response['task id']
            # if r_id in self.result: # write fresh results
            self.result[r_id]['meta_data']['result'] = result
