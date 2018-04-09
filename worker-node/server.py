from http.server import BaseHTTPRequestHandler, HTTPServer
# import SocketServer
import urllib.parse
from urllib.parse import urlparse, parse_qs, urlencode
# import subprocess
# import threading
import json
import cgi
import os

from worker import work

 
def startServer(port=8080):

    class S(BaseHTTPRequestHandler):
        def _set_headers(self):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

        def do_GET(self):
            parsed_path = urlparse(self.path)
            route = parsed_path.path
            params = parse_qs(parsed_path.query)

            if route == '/favicon.ico':
                self.send_response(200)
                self.end_headers()
                return 
            
            print("Params: ", params)

            worker_result = []      
            if not params:
                self.send_response(400)
                self.end_headers()
                worker_result = None
            else:
                self._set_headers()
                # Get treads and frequency (TR,FR)            
                tr = params.get("tr")[0]
                fr = params.get("fr")[0]
                # Launch main task. 
                worker_result = work(fr, tr)

            # return result
            self.wfile.write(json.dumps(
                {'json': 
                    {"GET - id": route, 
                    "Path": parsed_path, 
                    "Node:": os.environ['workername'], 
                    "Data": worker_result}
                }
            ).encode("utf-8"))

        def do_POST(self):
            ctype, pdict = cgi.parse_header(self.headers['content-type'])

            # refuse to receive non-json content
            if ctype != 'application/json':
                self.send_response(400)
                self.end_headers()
                return

            # TODO - write parcer for JSON responce from clients
            with open("client_responces.log", 'a') as logfile:
                try:
                    # get json from request data
                    self.json_data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                    #print key,value
                    for key,value in dict(self.json_data).items():
                        print (key + " - " + value)
                except:
                    pass      

            with open('WebServ.log', 'a') as logfile:
                logfile.write('%s - - [%s] %s\n'%
                                (self.client_address[0],
                                self.log_date_time_string(),
                                self.request))
            

            print ("Request: ", self.request)
            print ("Data: ", self.json_data)

            # return result 
            self._set_headers()           
            self.wfile.write(json.dumps(
                {'json': 
                    {"POST": pdict, "Node:": os.environ['workername'], "Data": self.json_data}
                }
            ).encode("utf-8"))

        # def do_HEAD(self):
        #     self._set_headers()
        


    def run(server_class=HTTPServer, handler_class=S, port=port):
        server_address = ('', port)
        httpd = server_class(server_address, handler_class)
        print('Starting httpd...')
        print(' ', server_address)
        
        httpd.serve_forever()
    
    run()

def readConfig(fileName='config.json'):
    try:
        with open(fileName, 'r') as cfile:
            config = json.loads(cfile.read())
            return config

    except IOError as e:
        print('No config file found!')
        print(e)
        return {}
    except ValueError as e:
        print('Invalid config file!')
        print(e)
        return {}

def run():
    #   Reading config file 
    conf = readConfig()
    if not conf:
        print('Unable to start script, no configuration!')
        return

    #   Starting http server to recieve responce from containers at background
    startServer()

if __name__ == "__main__": 
    run()