from flask import Flask, jsonify, request
from flask import render_template

from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room
import time

# USER
from logger.default_logger import BRISELogConfigurator
logger = BRISELogConfigurator().get_logger(__name__)

from tools.front_API import API
from main import run as main_run
# from tools.main_mock import run as main_run

import eventlet
eventlet.monkey_patch()

# instance of Flask app
app = Flask(__name__, static_url_path='', template_folder="static")
CORS(app)

# WebSocket
app.config['SECRET_KEY'] = 'galamaga'
socketio = SocketIO(app, logger=False, engineio_logger=True)
socketio.heartbeatTimeout = 15000

# Initialize the API singleton
API(api_object=socketio)

MAIN_PROCESS = None
data_header = {
    'version': '1.0'
}
# session id of clients
clients = []

# add clients in room
front_clients = []

@app.route('/')
def index():
    return render_template('index.html'), 200

# ---   START
@app.route('/main_start')
def main_process_start():
    """
    Verifies that Main-node is not running. 
    If free - creates new process with socketio instance and starts it.
    It ensures that for each run of main.py you will use only one socketio.

    If main process is already running - just return its status. (To terminate process - use relevant method).
    :return: main_process_status()
    """
    global MAIN_PROCESS, socketio

    if not MAIN_PROCESS:
        MAIN_PROCESS = eventlet.spawn(main_run)
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

# ---------------------------- Events ------------ 
@socketio.on('ping')
def ping_pong(json):
    logger.info(' Ping from: ' + str(request.sid))
    return 'main node: pong!'

# --------------
# managing array with curent clients
@socketio.on('connect') 
def connected():
    clients.append(request.sid)
    return "main: OK"

@socketio.on('disconnect')
def disconnect():
    clients.remove(request.sid)

# managing room with curent Front-end clients
@socketio.on('join', namespace='/front-end')
def on_join(data):
    room = data['room']
    logger.info("Main connection. Room", data)
    join_room(room)
    front_clients.append(request.sid)

@socketio.on('leave', namespace='/front-end')
def on_leave(data):
    room = data['room']
    leave_room(room)
    front_clients.remove(request.sid)

@socketio.on('disconnect', namespace='/front-end')
def front_disconnect():
    if request.sid in front_clients:
        front_clients.remove(request.sid)
# ------------------------------------------------


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=False, port=49152)
