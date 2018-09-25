__doc__ = """
Mock for main module for running BRISE configuration balancing."""

import pickle
import time
import random

from WorkerServiceClient.WSClient_sockets import WSClient
from tools.file_system_io import create_folder_if_not_exists
from model.model_selection import get_model

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
        with open("./tools/main_mock_dataNB.pkl", 'rb') as f:
            mock_data = pickle.loads(f.read())
    except IOError as e:
        print("Unable to load saved MOCK data: %s" % e)
        exit(1)

    sleep_between_messages = 0  # In seconds. One second + ~25 seconds to overall running for current version of mock.
    # ------------------------------------------------------
    # Scenario:
    # 1. Initial emits (the global and task configurations, the default configuration measurements results).
    # 2. Measuring the first set of configurations - 13.
    # 3. Building and validation of the first regression model.
    # 4. Prediction of a solution - this solution will not pass the validation (because it is worse than the default).
    # 5. Adding previous solution to the data set, measuring one new point.
    # 6. Building and validation of the second (and final) model.
    # 7. Prediction and validation of the solution.
    # 8. Reporting the results.
    # ------------------------------------------------------
    repetitions = 0
    tresholds = {'good': (4, 8),
                 'mid': (3, 4),
                 'bad': (2, 3)}
    create_folder_if_not_exists('./Results/')
    number_of_measured_configs = 0

    if io:
        # Sasha asked also to send each 'measuring' point to Worker Service.
        wsc = WSClient(mock_data["Task config"]["ExperimentsConfiguration"],
                       'w_service:8080',
                       "MOCK_WSC.log")
        # Sending global and task config
        temp = {"global_config": mock_data["Global config"], "task": mock_data["Task config"]}
        io.emit('main_config', temp)
        time.sleep(sleep_between_messages)
        print("Measuring default configuration that we will used in regression to evaluate solution... ")
        # Sending default configuration (like from the repeater) 10 times.
        for x in range(2):
            wsc.work(mock_data["Default config"][0])
            repetitions += 1
        number_of_measured_configs += 1
        io.emit('task result', {'configuration': mock_data["Default config"][0][0],
                                "result": mock_data["Default config"][1][0][0],
                                'number_of_configs': number_of_measured_configs
                                },)
        time.sleep(sleep_between_messages)

        # Sending results of default configuration measurement (like from the main).
        io.emit('default conf', {'configuration': mock_data["Default config"][0][0], "result": mock_data["Default config"][1][0][0]})
        time.sleep(sleep_between_messages)

        print("Measuring initial number experiments, while it is no sense in trying to create model"
              "\n(because there is no data)...")
        for feature, label in zip(mock_data["Features1"], mock_data["Labels1"]):
            print("Sending new task to IO.", end=' ')
            # if label < [406.12]: bounds = tresholds['good']
            # elif label < [1083.67]: bounds = tresholds['mid']
            # else: bounds = tresholds['bad']
            # repits = random.randint(*bounds)
            repits = 2
            repetitions += repits
            wsc.work([feature for x in range(repits)])
            number_of_measured_configs += 1
            io.emit('task result', {'configuration': feature,
                                    "result": label[0],
                                    'number_of_configs': number_of_measured_configs})
            time.sleep(sleep_between_messages)

        model = get_model(model_config=mock_data["Task config"]["ModelConfiguration"],
                      log_file_name="%s%s%s_model.txt" % (mock_data["Global config"]['results_storage'],
                                                          mock_data["Task config"]["ExperimentsConfiguration"]["WorkerConfiguration"]["ws_file"],
                                                          mock_data["Task config"]["ModelConfiguration"]["ModelType"]),
                      task_config=mock_data["Task config"])
        model.add_data(mock_data["Features1"], mock_data["Labels1"])
        model_built = model.build_model()
        # First model validation.
        model.validate_model(io, mock_data["Search space"])
        time.sleep(sleep_between_messages)

        # First model solution prediction (greater than default).
        predicted_labels, predicted_features = model.predict_solution(io, mock_data["Search space"])
        print("Predicted solution features:%s, labels:%s." % (str(predicted_features), str(predicted_labels)))
        io.emit('info', {'message': "Verifying solution that model gave.."})
        time.sleep(sleep_between_messages)

        # Sending additional configurations (including predicted configuration.
        add_features = [config for config in mock_data["Final feature set"] if config not in mock_data["Features1"]]
        add_labels = [result for result in mock_data["Final label set"] if result not in mock_data["Labels1"]]
        for feature, label in zip(add_features, add_labels):
            print("Sending new task to IO.", end=' ')
            if label < [406.12]: bounds = tresholds['good']
            elif label < [1083.67]: bounds = tresholds['mid']
            else: bounds = tresholds['bad']
            repits = random.randint(*bounds)
            repetitions += repits
            wsc.work([feature for x in range(repits)])
            number_of_measured_configs += 1
            io.emit('task result', {'configuration': feature,
                                    'result': label[0],
                                    'number_of_configs': number_of_measured_configs})
            time.sleep(sleep_between_messages)

        # Second (and final) model creation, validation, solution prediction.
        model = get_model(model_config=mock_data["Task config"]["ModelConfiguration"],
                      log_file_name="%s%s%s_model.txt" % (mock_data["Global config"]['results_storage'],
                                                          mock_data["Task config"]["ExperimentsConfiguration"]["WorkerConfiguration"]["ws_file"],
                                                          mock_data["Task config"]["ModelConfiguration"]["ModelType"]),
                      task_config=mock_data["Task config"])
        model.add_data(mock_data["Final feature set"], mock_data["Final label set"])
        model_built = model.build_model()
        # First model validation.
        model.validate_model(io, mock_data["Search space"])
        time.sleep(sleep_between_messages)
        predicted_labels, predicted_features = model.predict_solution(io, mock_data["Search space"])
        print("Predicted solution features:%s, labels:%s." % (str(predicted_features), str(predicted_labels)))
        time.sleep(sleep_between_messages)
        io.emit('info', {'message': "Verifying solution that model gave.."})
        time.sleep(sleep_between_messages)
        repits = random.randint(*tresholds['good'])
        [wsc._send_task([mock_data["Solution"][1]]) for x in range(repits)]
        repetitions += repits
        number_of_measured_configs += 1
        io.emit('task result', {
            'configuration': mock_data["Solution"][1],
            "result": mock_data["Solution"][0][0],
            'number_of_configs': number_of_measured_configs
        })
        time.sleep(sleep_between_messages)
        io.emit('info', {'message': "Solution validation success!"})
        time.sleep(sleep_between_messages)
        # reporting results
        repeater = A() # Just for reporting results. Fake object, in reporting only one field used.
        repeater.performed_measurements = repetitions    # Just for reporting results. These field used in reporting.
        model.get_result(repeater, io)


class A:
    @staticmethod
    def emit(*args):
        print("API MESSAGE: ", end='')
        print(args)


if __name__ == "__main__":
    """
    For the unit tests running - put following statements above WSClient importing:
from os import chdir
from os.path import abspath
from sys import path
chdir('..')
path.append(abspath('.'))
    """
    start = time.time()
    run(io=A())
    print("\n\nMock running time: %s(sec)." % round(time.time() - start))
