import os

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import socketio
import time
import pickle

# USER
from logger.default_logger import BRISELogConfigurator
import logging

logger = BRISELogConfigurator().get_logger(__name__)

from tools.front_API import API
from main import run as main_run
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

MAIN_PROCESS = None
data_header = {
    'version': '1.0'
}

# add clients in room
front_clients = []


# ---   START
@app.route('/main_start',  methods=['GET', 'POST'])
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
    global MAIN_PROCESS, socketio

    if not MAIN_PROCESS:
        if request.method == "POST":
            MAIN_PROCESS = eventlet.spawn(main_run, experiment_setup=pickle.loads(request.data))
        else:
            MAIN_PROCESS = eventlet.spawn(main_run)
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
    result = {}
    result['MAIN_PROCESS'] = {"main process": bool(MAIN_PROCESS),
                              "status": "running" if MAIN_PROCESS else 'none'}
    # Probably, we will have more processes at the BG.
    return jsonify(result)

# # ---   STOP
@app.route('/main_stop')
def main_process_stop():
    """
    Verifies if main process running and if it is - terminates it using process.join() method with timeout = 5 seconds.
    After it returns status of this process (should be terminated).
    :return: main_process_status()
    """
    global MAIN_PROCESS

    if MAIN_PROCESS:
        MAIN_PROCESS.cancel()
        eventlet.kill(MAIN_PROCESS)
        MAIN_PROCESS = None
        time.sleep(0.5)

    return main_process_status()

@app.route('/download_dump/<file_format>')
def download_dump(file_format):
    dump_name = os.environ.get('EXP_DUMP_NAME')
    try:
        if(dump_name == 'undefined'):
            return jsonify(message='missing experiment file', href='#')
        else:
            filename = "{name}.{format}".format(
                name=dump_name, format=file_format)
            return send_from_directory('/root/Results/serialized/', filename, as_attachment=True)
    except Exception as error:
        logger.error('Download dump file of the experiment: %s' % error)
        return str(error)

# ---------------------------- Events ------------
@socketIO.on('ping')
def ping_pong(sid, json):
    logger.info(' Ping from: ' + str(sid))
    return 'main node: pong!'

# --------------

# managing room with curent Front-end clients
@socketIO.on('join', namespace='/front-end')
def on_join(sid, data):
    room = data['room']
    logger.info("Main connection. Room", data = data)
    socketIO.enter_room(sid, room)
    front_clients.append(sid)

@socketIO.on('leave', namespace='/front-end')
def on_leave(sid, data):
    room = data['room']
    socketIO.leave_room(sid, room)
    front_clients.remove(sid)

# ------------------------------------------------


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 49152)), app)
