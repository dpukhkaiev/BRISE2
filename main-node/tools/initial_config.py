__doc__ = """
    Module to read config and tasks for execute."""
import json
from tools.file_system_io import load_json_file, create_folder_if_not_exists


def read_global_config(global_config_path):
    """
    Method reads configuration for BRISE from GlobalConfig.json configuration file.
    :param global_config_path: sting path to file.
    :return: dict with configuration for BRISE
    """
    try:
        config = load_json_file(global_config_path)
        return config

    except IOError as e:
        print('No config file found!')
        print(e)
        exit(3)
    except ValueError as e:
        print('Invalid config file!')
        print(e)
        exit(3)


def load_task(path_to_file="./Resources/task.json"):
    """
    Method reads task configuration from task.json file.
    :param path_to_file: sting path to task file.
    :return: dict with task parameters and task data.
    """
    try:
        task = load_json_file(path_to_file)
        data = load_json_file(task["DomainDescription"]["DataFile"])
        taskDataPoints = []
        for dimension in task["DomainDescription"]["FeatureNames"]:
            taskDataPoints.append(data[dimension])
        task["DomainDescription"]["AllConfigurations"] = taskDataPoints
    except IOError as e:
        print("Error with reading task.json file: %s" % e)
        exit(1)
    except json.JSONDecodeError as e:
        print("Error with decoding task: %s" % e)
        exit(1)
    return task


def initialize_config(argv):
    """
    Load global config and task config.
    :return: (dict globalConfiguration, dict taskConfiguration)
    """
    taskPath = argv[1] if len(argv) > 1 else './Resources/task.json'
    global_config_path = argv[2] if len(argv) > 2 else './GlobalConfig.json'
    print(taskPath, global_config_path)
    #   Reading config file
    print("Global BRISE configuration file: |%s|, task description file: |%s|" % (global_config_path, taskPath))
    globalConfig = read_global_config(global_config_path)

    #   Loading task config and creating config points distribution according to Sobol.
    # {"task_name": String, "params": Dict, "taskDataPoints": List of points }
    task = load_task(taskPath)
    create_folder_if_not_exists(globalConfig['results_storage'])

    return globalConfig, task
