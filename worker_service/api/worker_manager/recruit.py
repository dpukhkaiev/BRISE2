import os
import requests

# import threading
import time
from random import randint
from concurrent.futures import ThreadPoolExecutor


# LOGIN
import logging
# logging.basicConfig(filename='recruit.log',level=logging.DEBUG)

class Recruit():
    '''
    Class for discovering/managing workers
    '''
     
    def __init__(self, flow):
        # Set how much workers we have
        self.workers = ['alpha', 'beta', 'gamma', 'delta'][:int(os.getenv('WORKER_COUNT'))]
        self.flow = flow
        self.result = dict()
        self._executor = ThreadPoolExecutor(1).submit(self._loop)

    def __del__(self):
        self._executor.cancel()

    def _loop(self):
        while True: 
            # wait task in queue
            time.sleep(2) 
            self.fetch_res()
            if self.flow.stack.queue:
                # if there is a task(s) in the queue
                print(" Spin:", self.spin())
                time.sleep(1)

    def status(self):
        print(" Workers:", self.workers)

    def results(self, id=False):
        if id: 
          return self.result[id] if id in self.result else None 
        else: return self.result

    def results_2(self, struct):
        answer = {
            "response_type": "get_results",
            "task_name": [],
            "param_values": [],
            "statuses": [],
            "params_names": struct["response_struct"]
        }

        for i in struct["id"]:
            temp = self.result[i] 
            answer["task_name"].append(temp["run"]["method"])
            answer["statuses"].append("done" if temp["meta_data"]["result"] else "in progress")
            
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
        return answer


    ''' PUT ==>
    {
        "task_name": "random_1",
        "request_type": "get_results",
        "response_struct": ["frequency", "threads", "time" ],
        "ID": [123123123, 123123124, 123123125]
    }
    '''

    ''' <==
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
    }

    '''


    def assign_test(self):
        payload = {'fr': '2700.0', 'tr': '32'}
        r = requests.get('http://'+ self.workers[1] +':8080', params=payload)
        print(" Assign Go!\n Result:", r.json())        
        return r.json()

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
            # get results from workers
            # print ("Res ::\n", self.result)            
            
            self.fetch_res()

            # try assign a task to worker          
            r = requests.post('http://'+ self.workers[w_random] +':8080/run', json=payload)
            if r.json()['status'] == 'run':
                self.result[payload['id']]['meta_data']['accept'] = time.time()
                self.result[payload['id']]['meta_data']['appointment'] = r.json()['node']
                send = True
                task = None
                return r.json(), r.status_code
            else:
                time.sleep(1)

    def fetch_res(self):
        for worker in self.workers:
            r = requests.get('http://'+ worker +':8080')
            result = r.json()['result']
            if result is not "null": # if worker have results
                r_id = r.json()['id']
                if r_id in self.result: # write fresh results
                    self.result[r_id]['meta_data']['result'] = result
