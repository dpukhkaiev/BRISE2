#!/usr/bin/env python3

from main import run as main_run
from flask import Flask, jsonify
from multiprocessing import Process, Queue
import time

app = Flask(__name__)

# hide HTTP request logs
import logging
log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

DATA_STORAGE = {
    "BRISE_VERSION": 1,
}
MAIN_PROCESS = Process(name='null')
MAIN_PROCESS_QUEUE = Queue()

@app.route('/get_data')
def get_data():
    """
    Takes shared between processes Queue (MAIN_PROCESS_QUEUE), check if new data is available,
    read all of it and return as json response.
    :return: JSONIFY OBJECT
    """
    global MAIN_PROCESS_QUEUE, DATA_STORAGE
    while not MAIN_PROCESS_QUEUE.empty():
        DATA_STORAGE.update(MAIN_PROCESS_QUEUE.get_nowait())
    return jsonify(DATA_STORAGE)


@app.route('/main_process_status')
def main_process_status():
    """
    Returns json response that contains status of main process.
    If more processes will be added - could be modified to display relevant info.
    :return: JSONIFY OBJECT
    """
    result = {}
    result['MAIN_PROCESS'] = {"Name": MAIN_PROCESS.name,
                                 "Exit code": MAIN_PROCESS.exitcode if not MAIN_PROCESS.is_alive() else None,
                                 "Status": "Running" if MAIN_PROCESS.is_alive() else "Not running"}
    # Probably, we will have more processes at the BG.
    return jsonify(result)


@app.route('/main_process_start')
def main_process_start():
    """
    Verifies that MAIN_PROCESS is not running. If not - creates needed MAIN_PROCESS_QUEUE,
    creates new process with this Queue and starts it.
    It ensures that for each run of main.py you will use only one Queue.

    If main process is already running - just return its status. (To terminate process - use relevant method).
    :return: main_process_status()
    """
    global MAIN_PROCESS, MAIN_PROCESS_QUEUE

    if not MAIN_PROCESS.is_alive():
        MAIN_PROCESS_QUEUE = Queue()
        MAIN_PROCESS = Process(target=main_run, name="main.run()", args=(MAIN_PROCESS_QUEUE,))
        MAIN_PROCESS.start()

    return main_process_status()


@app.route('/main_process_stop')
def main_process_stop():
    """
    Verifies if main process running and if it is - terminates it using process.join() method with timeout = 5 seconds.
    After it returns status of this process (should be terminated).
    :return: main_process_status()
    """
    global MAIN_PROCESS

    if MAIN_PROCESS.is_alive():
        MAIN_PROCESS.terminate()
        MAIN_PROCESS_QUEUE.close()
        time.sleep(0.5)

    return main_process_status()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


