def params_to_string(task: dict) -> dict:
    for k in task['parameters'].keys():
        if (isinstance(task['parameters'][k], int) or isinstance(task['parameters'][k], float)):
            task['parameters'][k] = str(task['parameters'][k])
    return task