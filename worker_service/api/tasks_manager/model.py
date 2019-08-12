from flask import jsonify
import time
import uuid

class Task():
    '''
     The basic working unit that executed by the workers
    '''

    def __init__(self, method, params, conf="null", owner="null", appointment="null", receive="null", accept="null", result="null"):
        self.id = uuid.uuid4().hex
        self.run = {
           'method': method,
           'param': params
        }
        self.conf = conf
        self.meta = {
            'owner': owner,
            'appointment': appointment,
            'receive': receive,
            'accept': accept,
            'result': result 
        }  

    def to_json(self):
        return {
            'id': self.id,
            'run': self.run,
            'config': self.conf,
            'meta_data': self.meta
        }


def t_parser(payload): 
    # Parse json data in to Task objects
    task_list = list()
    id_list = list()    
    for method in payload:
        par = method['params']
        par['ws_file'] = method['worker_config']['ws_file']
        new = Task(method=method['task_name'],params=par,conf=method['worker_config'],receive=time.time())        
        task_list.append(new)
        id_list.append(new.id)
    return id_list, task_list

def t_parser_2(payload): 
    # Parse json data in to Task objects. Special for the Jeka regresion
    task_list = list()
    id_list = list()
    for values in payload["param_values"]:
        p_unit = dict(zip(payload["params_names"], values))
        p_unit.update(dict(payload["worker_config"]))
        new = Task(method=payload['task_name'],params=p_unit,conf=payload['worker_config'],receive=time.time())        
        task_list.append(new)
        id_list.append(new.id)
    return id_list, task_list



class Stack():
    '''
    Stack for task execution.
    Define methods to manage task queue.
    '''

    def __init__(self):
        self.queue = list()

    def to_json(self):
        temp = list()
        for task in self.queue:
            temp.append(task.to_json())
        return temp or []

    def pop(self):
        # remove first task from queue
        return self.queue.pop(0) if len(self.queue) > 0 else None

    
    def push(self, task, index=0):
        index=len(self.queue)
        self.queue.insert(index, task)
    
    def get(self, index=0):
        # returns a task with an index
        if len(self.queue) > 0 and index < len(self.queue):
            return self.queue[index]
        else:
            return None


        