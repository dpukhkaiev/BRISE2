import os

from flask import Flask 

def create_app(script_info=None):

    # instantiate the app
    app = Flask(__name__)

    # register blueprints
    from api.router import service_blueprint
    app.register_blueprint(service_blueprint)

    return app

