# worker_service/intro.py
import eventlet
import eventlet.wsgi
from flask.cli import FlaskGroup
from flask import jsonify, Flask

# config
from __init__ import create_app, setup_logging

# initialization
setup_logging()
socketio, app = create_app()

# Run server
if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 49153)), app)
