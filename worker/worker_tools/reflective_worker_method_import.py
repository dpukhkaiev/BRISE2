import difflib
import importlib
import inspect
import logging
import os

# TODO shared library from main-node.tools wish adaptation for worker


def get_worker_methods(found_module):
    """
    Goes through `found_module` and find all methods(functions) in it.

    :param found_module: python module.

    :return: list of tuples (function_name:str, function_obj:function)
    """
    logger = logging.getLogger(__name__)

    try:
        # Getting the functions
        methods_in_module = inspect.getmembers(found_module,
                                               lambda member: inspect.isfunction(member))
        # methods_in_module is a list of tuples (function_name:str, function_obj:function)
    except Exception as error:
        msg = "Error occurred when looking for a worker methods. Following exception occurred: %s" % (error)
        logger.error(msg)
        raise Exception(msg)

    return methods_in_module


def get_worker_module():
    """
    Get `worker` module from `worker.py` file and import them.

    :return: imported module and path to the module
    """
    logger = logging.getLogger(__name__)

    # Finding a Module
    selected_module_file_name = ''
    cutoff = 1
    module_name = 'worker'
    reduction_step = 0.1
    files = os.listdir()
    if not files:
        # TODO: aspect weaving logging and debug info before every raise?
        #  Or maybe raising some specific Exception (with behavior) and catching it in API to handle expected errors:
        #  propagation to the front, dumping locals, saving stack (logger.error()and etc..
        msg = "Specified directory is empty."
        logger.error(msg)
        raise NameError(msg)
    while not selected_module_file_name:
        selected_module_file_name = difflib.get_close_matches(module_name, files, n=1, cutoff=cutoff)
        cutoff -= reduction_step
    logger.debug("'%s' module was selected with cutoff=%f for name=%s." %
                 (selected_module_file_name, cutoff, module_name))
    module_path = selected_module_file_name[0][:-3]
    try:
        found_module = importlib.import_module(module_path)
    except ImportError as error:
        msg = "Unable to import module %s. Following exception occurred: %s" % (module_path, error)
        logger.error(msg)
        raise ImportError(msg)
    return found_module, module_path


def get_worker_methods_as_dict():
    """
    Creates a dict with the name of the task and the corresponding method that performs this task.

    :return: dict with `task_name` as a key and function as value
    """
    dict_worker_methods = {}
    worker_module, module_path = get_worker_module()
    for method in get_worker_methods(worker_module):
        dict_worker_methods[method[0]] = method[1]
    return dict_worker_methods
