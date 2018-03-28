import docker

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import json
import urlparse
import subprocess
import threading
import json
import time

def runRemoteContainer(host):

    # Creating client object that reflects connection to remote docker daemon
    try:
        client = docker.DockerClient(
            base_url='tcp://' + host['ip'] + ':' + str(host['port']))
        pingIsOk = client.ping()
        
        if pingIsOk: print "Ping is OK, remote daemon %s is available!" % host['ip']
        else:
            print "Unable to recieve proper ping responce from %s, check script/docker configuration." % host['ip']
            # return 1

    except docker.errors.APIError as e:
        print e
        # return 1
    
    # Running docker container on remote host.
    # TODO - change it to building normal container from normal dockerfile that will copy all needed files to remote host and rung entry point (Python script)
    container = client.containers.run(image='alpine', command="echo Success!", detach=True)
    # containerLogs = 
    print "Container logs:"
    print container.logs()
    # return 0

def startServer(port=8089):

    class S(BaseHTTPRequestHandler):
        def _set_headers(self):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

        def do_GET(self):
            self._set_headers()
            parsed_path = urlparse.urlparse(self.path)
            request_id = parsed_path.path
            
            self.wfile.write("Hello\nRequest ID:%s\npath:%s" % (request_id, parsed_path))

        def do_POST(self):
            self._set_headers()
            parsed_path = urlparse.urlparse(self.path)
            request_id = parsed_path.path

            # TODO - write parcer for JSON responce from clients
            with open("client_responces.log", 'a') as logfile:
                try:
                    
                    request = self.request


            with open('WebServ.log', 'a') as logfile:
                logfile.write('%s - - [%s] %s\n'%
                                (self.client_address[0],
                                self.log_date_time_string(),
                                self.request))
            
            self.wfile.write("Hello\nRequest ID:%s\npath:%s" % (request_id, parsed_path))

        def do_HEAD(self):
            self._set_headers()
        


    def run(server_class=HTTPServer, handler_class=S, port=port):
        server_address = ('', port)
        httpd = server_class(server_address, handler_class)
        print 'Starting httpd...'
        httpd.serve_forever()
    
    run()

def readConfig(fileName='config.json'):
    try:
        with open(fileName, 'r') as cfile:
            config = json.loads(cfile.read())
            return config

    except IOError as e:
        print 'No config file found!'
        print e
        return {}
    except ValueError as e:
        print 'Invalid config file!'
        print e
        return {}

def run():

    #   Reading config file 
    remoteDaemons = readConfig()
    if not remoteDaemons:
        print 'Unable to start script, no configuration!'
        return

    #   Starting http server to recieve responce from containers at background
    server_thread = threading.Thread(target=startServer)
    server_thread.start()
    time.sleep(2) # to start a httpd
    

    #   Start runnig containters on remote daemons
    for container in remoteDaemons.keys():
        runRemoteContainer(remoteDaemons[container])

    #   After finishing running containers - join server thread to main thread
    server_thread.join()

if __name__ == "__main__":
    run()