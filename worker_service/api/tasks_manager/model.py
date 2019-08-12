from flask import jsonify
import time
import uuid

class Task():
    '''
     The basic working unit that executed by the workers
    '''

    def __init__(self, method, params, scenario="null", owner="null", appointment="null", receive="null", accept="null", result="null"):
        self.id = uuid.uuid4().hex
        self.run = {
           'method': method,
           'param': params
        }
        self.scenario = scenario
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
            'scenario': self.scenario,
            'meta_data': self.meta
        }


def task_parser(tasks):
    """
    Method parses data from `tasks` parameter into Task objects and adds tasks to `task_list`.
    :param tasks: list of dictionaries that represent tasks for workers.
    :return: list with ids and list of tasks.
    """
    # Parse json data in to Task objects
    task_list = list()
    id_list = list()    
    for task in tasks:
        par = task['params']
        new = Task(method=task['task_name'],params=par,scenario=task['scenario'],receive=time.time())
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


        