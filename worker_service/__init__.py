import os

from flask import Flask 
from flask_cors import CORS

def create_app(script_info=None):

    # instantiate the app
    app = Flask(__name__)
    CORS(app) # !!! 

    # register blueprints
    from api.router import service_blueprint
    app.register_blueprint(service_blueprint)

    return app

