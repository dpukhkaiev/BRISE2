# worker_service/intro.py

from flask.cli import FlaskGroup
from flask import jsonify, Flask

# config
from __init__ import create_app

# initialization 
app = create_app()

# Run server
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=80,debug=True)

