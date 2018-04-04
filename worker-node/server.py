from http.server import BaseHTTPRequestHandler, HTTPServer
# import SocketServer
import urllib.parse
from urllib.parse import urlparse, parse_qs, urlencode
# import subprocess
# import threading
import json
# import time

from worker import work

 
def startServer(port=8080):

    class S(BaseHTTPRequestHandler):
        def _set_headers(self):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

        def do_GET(self):
            self._set_headers()
            parsed_path = urlparse(self.path)
            route = parsed_path.path
            params = parse_qs(parsed_path.query)
            
            worker_result = []
            # Get treads and frequency (TR,FR)
            print("Params: ", params)
            if params is not None:   
                tr = params.get("tr")[0]
                fr = params.get("fr")[0]
                print("Keys: ", type(tr), type(fr))
                # Launch main task. 
                worker_result = work(fr, tr)

            self.wfile.write(json.dumps(
                {'json': 
                    {"GET - id": route, "Path": parsed_path, "Data": worker_result}
                }
            ).encode("utf-8"))

        def do_POST(self):
            self._set_headers()
            parsed_path = urllib.parse.urlparse(self.path)
            request_id = parsed_path.path

            # TODO - write parcer for JSON responce from clients
            with open("client_responces.log", 'a') as logfile:
                try:
                    
                    request = self.request
                except:
                    pass
                    

            with open('WebServ.log', 'a') as logfile:
                logfile.write('%s - - [%s] %s\n'%
                                (self.client_address[0],
                                self.log_date_time_string(),
                                self.request))
            
            self.wfile.write(json.dumps(
                {'json': 
                    {"POST - id": request_id, "Path": parsed_path, "Data": worcer_result}
                }
            ).encode("utf-8"))

        def do_HEAD(self):
            self._set_headers()
        


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