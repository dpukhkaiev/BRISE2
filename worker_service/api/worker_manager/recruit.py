import os
import requests
import threading

import eventlet
eventlet.monkey_patch()

# from flask_socketio import SocketIO, send, emit
import time
from random import randint
from concurrent.futures import ThreadPoolExecutor


# LOGIN
import logging
# logging.basicConfig(filename='recruit.log',level=logging.DEBUG)
logging.getLogger('socketio').setLevel(logging.DEBUG)
logging.getLogger('engineio').setLevel(logging.DEBUG)


class Recruit():
    '''
    Class for discovering/managing workers
    '''
     
    def __init__(self, flow, socket):
        self.workers = []
        self.flow = flow
        self.socket = socket

        self.result = dict()
        # success flag
        self.send = True
        self.focus_task = None

        eventlet.spawn(self._loop)

    # def __del__(self):
    #     self._executor.cancel()

    def _loop(self):
        while True: 
            # wait task in queue
            eventlet.sleep(1)

            if self.flow.stack.queue:
                # if there is a task(s) in the queue
                self.spin()
                time.sleep(1)

    def status(self):
        print(" Workers:", self.workers)

    def new_task(self, item):
        if item.id not in self.result:
            self.result[item.id] = item.to_json()
            self.flow.add_task(item)

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
        ''' Pull out a task from the Stack and find a worker who can complete it
        '''

        self.focus_task = self.flow.pull_task()
        payload = self.focus_task.to_json()
        # store task id - status
        if payload:
            self.result[payload['id']] = payload

        # success flag
        self.send = False  

        while self.focus_task and not self.send:
            # TODO it is necessary to form a structure that monitors free workers
            eventlet.sleep(1)
            if len(self.workers):
                k = randint(0, 9)%len(self.workers)
                print(" Task send to", self.workers[k])
                self.socket.emit('assign', payload, namespace='/task', room=self.workers[k])

    def task_confirm(self, obj):
        if obj['status'] == 'run':
            self.result[obj['task id']]['meta_data']['accept'] = time.time()
            self.result[obj['task id']]['meta_data']['appointment'] = obj['node']

            self.socket.emit('in progress', obj, room='/front-end', namespace='/front-end')
            self.send = True
            self.focus_task = None
        else:
            print('Worker did not confirm a task')

    def analysis_res(self, json_response):
        result = json_response['result']
        if result is not "null": # if worker have results
            r_id = json_response['task id']
            # if r_id in self.result: # write fresh results
            self.result[r_id]['meta_data']['result'] = result
            return r_id

