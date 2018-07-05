__doc__ = """
Module to read config and tasks for execute
"""
import json
from tools.file_system_io import load_json_file, create_folder_if_not_exists

def readGlobalConfig(fileName):
    try:
        config = load_json_file(fileName)
        return config

    except IOError as e:
        print('No config file found!')
        print(e)
        # return {}
        exit(3)
    except ValueError as e:
        print('Invalid config file!')
        print(e)
        # return {}
        exit(3)

def load_task(path_to_file="./Resources/task.json"):
    """
    Method reads task.json file where task name and task parameters, that are needed to be sent to the workers specified.
    :param path_to_file: sting path to task file.
    :return: dict with task name, task parameters and task data in ndarray
    """
    try:
        task = load_json_file(path_to_file)
        data = load_json_file(task["params"]["DataFile"])
        taskDataPoints = []
        for dimension in task["params"]["FeatureNames"]:
            taskDataPoints.append(data["all_data"][dimension])
    except IOError as e:
        print("Error with reading task.json file: %s" % e)
        exit(1)
    except json.JSONDecodeError as e:
        print("Error with decoding task: %s" % e)
        exit(1)
    return {"task_name"         : task["task_name"],
            "params"            : task["params"],
            "TaskDataPoints"    : taskDataPoints,
            "default_point"      : data["default_point"]}

def initialize_config(globalConfigPath='./GlobalConfig.json', taskPath="./Resources/NB/taskNB1.json"):
    """
    Method reads .json file
    :param path_to_file: sting path to file.
    :return: object that represent .json file
    """
    #   Reading config file 
    globalConfig = readGlobalConfig(globalConfigPath)

    #   Loading task config and creating config points distribution according to Sobol.
    # {"task_name": String, "params": Dict, "taskDataPoints": List of points }
    task = load_task(taskPath)
    create_folder_if_not_exists(globalConfig['results_storage'])

    return globalConfig, task