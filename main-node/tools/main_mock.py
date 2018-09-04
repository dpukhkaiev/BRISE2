__doc__ = """
Mock for main module for running BRISE configuration balancing."""

import pickle
import time
from os import chdir
from os.path import abspath
from sys import path


def run(io=None):
    """
    Structure saved data:
    model_and_data = {
        "Search space": list
        "Validated model": regression model object. dumped just after successful model validation
        "Model with validated solution": regression model object.
        "Final feature set": list. - feature set that was before final report and exit
        "Final label set": list
        "Solution": list - final reported configuration and energy
        "Global config": dict
        "Task config": dict 
    }
    """
    try:
        with open("./tools/main_mock_data.pkl", 'rb') as f:
            model_and_data = pickle.loads(f.read())
    except IOError as e:
        print("Unable to load saved MOCK data: %s" % e)
        exit(1)

    sleep_between_messages = 1

    global_config = model_and_data["Global config"]
    task_config = model_and_data["Task config"]
    search_space = model_and_data["Search space"]
    saved_features = model_and_data["Final feature set"]
    saved_labels = model_and_data["Final label set"]
    saved_validated_model = model_and_data["Validated model"]
    saved_solution = model_and_data["Solution"]

    if io:
        temp = {"global_config": global_config, "task": task_config}
        io.emit('main_config', temp)
        print("Measuring default configuration that we will used in regression to evaluate solution... ")
        io.emit('task result', {'configuration': [2900.0, 32], "result": 309.05})
        time.sleep(sleep_between_messages)

        # from main.py
        io.emit('default conf', {'configuration': [2900.0, 32], "result": 309.05})
        time.sleep(sleep_between_messages)

        print("Measuring initial number experiments, while it is no sense in trying to create model"
              "\n(because there is no data)...")

        for x in range(task_config["SelectionAlgorithm"]["NumberOfInitialExperiments"]):
            print("Sending new task to IO.")
            io.emit('task result', {'configuration': saved_features[x], "result": saved_labels[x][0]})
            time.sleep(sleep_between_messages)

        # model validation
        io.emit('info', {'message': "Verifying solution that model gave.."})
        saved_validated_model.validate_model(io=io, search_space=search_space)
        time.sleep(sleep_between_messages)
        # prediction of solution
        predicted_labels, predicted_features = saved_validated_model.predict_solution(io=io, search_space=search_space)
        print("Predicted solution features:%s, labels:%s." % (str(predicted_features), str(predicted_labels)))
        time.sleep(sleep_between_messages)
        io.emit('info', {'message': "Verifying solution that model gave.."})
        io.emit('task result', {'configuration': saved_solution[1], "result": saved_solution[0][0]})
        time.sleep(sleep_between_messages)
        io.emit('info', {'message': "Solution validation success!"})
        # reporting results
        temp_message = "Reporting some final stuff from MOCK.."
        io.emit('info', {'message': temp_message, "quality": saved_solution[0], "conf": saved_solution[1]})
        time.sleep(sleep_between_messages)
        temp = {"best point": {'configuration': saved_solution[1],
                               "result": saved_solution[0][0],
                               "measured points": saved_features}
                }
        io.emit('best point', temp)


class A:
    @staticmethod
    def emit(*args):
        print(args)


if __name__ == "__main__":
    chdir('..')
    path.append(abspath('.'))
    run(io=A())
