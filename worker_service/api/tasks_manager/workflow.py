
from .model import Task, Stack

class Workflow():
    '''
    Description logic to manage tasks stack
    Define rules how to work with Stack, the majority of tasks and workers
    '''

    def __init__(self):
        self.stack = Stack()
        self.add_task(Task('random', 42, owner=1)) # Test instance
        self.add_task(Task('random', 42, owner=2)) # Test instance


    def add_task(self, task):
        self.stack.push(task)

    def pull_task(self):
        # TODO add  priority in the tasks execution.
        # remove from stack
        return self.stack.pop()

    def get_task(self, index=0):
        # get task copy from stack
        return self.stack.get(index)

    def go_go_baby(self):
        # debug method
        # use '__dict__' to return valid data
        return self.stack.pop().__dict__ 

    def get_stack(self):
        return self.stack.to_json() or {}