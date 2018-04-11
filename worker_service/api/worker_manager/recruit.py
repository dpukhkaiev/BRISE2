import os
import requests

import threading
import time

class Recruit():
    '''
    Class for discovering/managing workers
    '''
     
    def __init__(self, flow):
        # Set how much workers we have
        self.workers = ['alpha', 'beta', 'gamma', 'delta'][:int(os.getenv('WORKER_COUNT'))]
        self.flow = flow
        # daemon_loop(self.flow)

    def print(self):
        print(" Workers:", self.workers)

    def assign_test(self):
        payload = {'fr': '2700.0', 'tr': '32'}
        r = requests.get('http://'+ self.workers[1] +':8080', params=payload)
        # log(r)
        return r.json()

    def assign(self):
        payload = self.flow.get_task().to_json()
        r = requests.post('http://'+ self.workers[0] +':8080', json=payload)
        return r.json()


# Log history
def log(r):
    ''' Login for workers response
    '''
    with open('recruit.log', 'ws') as logfile:
        for chunk in r.iter_content(chunk_size=128):
            logfile.write(chunk)
