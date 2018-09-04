# worker_service/intro.py

from flask.cli import FlaskGroup
from flask import jsonify, Flask

# config
from __init__ import create_app

# initialization 
socketio, app = create_app()

# Run server
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True, port=8080)