#!/usr/bin/env python3

from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'hello_world'

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
