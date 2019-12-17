import os

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import socketio
import time
import pickle
from threading import Thread
# USER
from logger.default_logger import BRISELogConfigurator
import logging

logger = BRISELogConfigurator().get_logger(__name__)

import eventlet.debug

eventlet.monkey_patch()
eventlet.debug.hub_prevent_multiple_readers(False)

from tools.front_API import API
from main import MainThread
# from tools.main_mock import run as main_run

import eventlet

eventlet.monkey_patch()

socketio_logger = logging.getLogger("SocketIO")
engineio_logger = logging.getLogger("EngineIO")
socketio_logger.setLevel(logging.WARNING)
engineio_logger.setLevel(logging.WARNING)

socketIO = socketio.Server(ping_timeout=300, logger=socketio_logger, engineio_logger=engineio_logger)
# instance of Flask app
app = Flask(__name__, static_url_path='', template_folder="static")
CORS(app)
app.wsgi_app = socketio.WSGIApp(socketIO, app.wsgi_app)

# WebSocket
app.config['SECRET_KEY'] = 'galamaga'

# Initialize the API singleton
API(api_object=socketIO)

MAIN_THREAD: Thread = MainThread()
data_header = {
    'version': '1.0'
}


# ---   START
@app.route('/main_start', methods=['GET', 'POST'])
def main_process_start():
    """
    Verifies that Main-node is not running.
    If free - creates new process with socketio instance and starts it.
    It ensures that for each run of main.py you will use only one socketio.

    HTTP GET: Start BRISE without providing Experiment Description - BRISE will use the default one.
    HTTP POST: Start BRISE with provided Experiment Description and search space as a `JSON` payload and data attached to request.

    If main process is already running - just return its status. (To terminate process - use relevant method).
    :return: main_process_status()
    """
    global MAIN_THREAD

    if MAIN_THREAD.get_state() == MainThread.State.IDLE:
        if request.method == "POST":
            MAIN_THREAD = MainThread(experiment_setup=pickle.loads(request.data))
            MAIN_THREAD.start()
        else:
            MAIN_THREAD = MainThread()
            MAIN_THREAD.start()
            logger.info(request.method)
        time.sleep(0.1)

    return main_process_status()


# ---   STATUS
@app.route('/status')
def main_process_status():
    """
    Returns json response that contains status of main process.
    If more processes will be added - could be modified to display relevant info.
    :return: JSONIFY OBJECT
    """
    global MAIN_THREAD
    result = {}
    main_thread_state = MainThread.State.IDLE

    while True:
        main_thread_state = MAIN_THREAD.get_state()
        if main_thread_state != MainThread.State.SHUTTING_DOWN:
            break
    if main_thread_state == MainThread.State.IDLE:
        result['MAIN_PROCESS'] = {"main process": bool(False),
                                  "status": 'none'}
    elif main_thread_state == MainThread.State.RUNNING:
        result['MAIN_PROCESS'] = {"main process": bool(True),
                                  "status": 'running'}
    return jsonify(result)


# # ---   STOP
@app.route('/main_stop')
def main_process_stop():
    """
    Verifies if main process running and if it is - terminates it using process.join() method with timeout = 5 seconds.
    After it returns status of this process (should be terminated).
    :return: main_process_status()
    """
    global MAIN_THREAD

    if MAIN_THREAD.get_state() == MainThread.State.RUNNING:
        MAIN_THREAD.stop()

    return main_process_status()


@app.route('/download_dump/<file_format>')
def download_dump(file_format):
    dump_name = os.environ.get('EXP_DUMP_NAME')
    try:
        if (dump_name == 'undefined'):
            return jsonify(message='missing experiment file', href='#')
        else:
            filename = "{name}.{format}".format(
                name=dump_name, format=file_format)
            return send_from_directory('/root/Results/serialized/', filename, as_attachment=True)
    except Exception as error:
        logger.error('Download dump file of the experiment: %s' % error)
        return str(error)


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 49152)), app)
