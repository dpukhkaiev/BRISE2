#!/usr/bin/env python3

from flask import Flask
import csv

app = Flask(__name__)

# hide HTTP request logs
import logging
log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)


#with open ('random_1_1_results.csv', 'r') as csvfile:



@app.route('/')
def hello_world():
    return 'hello_world_new'

@app.route('/test')
def first_test():
    return 'Go go! Test'


# @app.route('/results', methods=['GET', 'POST', 'SET'])
# def results_to_json():
#     x = []
#     with open('random_1_1_results.csv') as f_csv:
#         for x in f_csv:
#             x = x.split()

#     return {
#         x[0]
#     }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=1234)


