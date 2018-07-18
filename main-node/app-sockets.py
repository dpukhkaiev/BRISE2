#!/usr/bin/env python3
from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit
import multiprocessing
from multiprocessing import Process, Manager, Queue
import time
import socket


# hide HTTP request logs
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.DEBUG)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# hide HTTP request logs
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

IP = '0.0.0.0'
PORT = 9090    

def func(q, data):
    q.put(data)

@socketio.on('message')
def handleMessage(msg):
    
    ###  Connection to the client (main)  ###
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Default address family, socket type
    address = (IP, PORT)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(address)
    server.listen(5)   # The maximum number of queued connections
    data = "[*] Started listening on " + str(IP) + " : " + str(PORT)
    send(data, broadcast=True)
    
    while True:
        
        client, addr = server.accept()
        data = "[*] Get a connection from " + str(addr[0]) + " : " + str(addr[1])
        send(data, broadcast=True)
        start_connection = "ready".encode()
        client.send(start_connection)

        while True:
            data = client.recv(1024).decode()
            if (data == "goodbye"):
                msg = "closed"
                send(msg, broadcast=True)
                close_connection = "close".encode()
                client.send(close_connection)
                client.close()
                break
            else:
                request = "got".encode()
                client.send(request)
                send(data, broadcast=True)

 
if __name__ == '__main__':
	socketio.run(app, host='0.0.0.0', port='5000')