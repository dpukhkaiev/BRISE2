from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
# import SocketServer
import urlparse
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
            parsed_path = urlparse.urlparse(self.path)
            request_id = parsed_path.path
            csv_data = work()
            
            self.wfile.write({'json': 
                json.dumps({"ID": request_id, "Path": parsed_path, "Data": csv_data})
            })

        def do_POST(self):
            self._set_headers()
            parsed_path = urlparse.urlparse(self.path)
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
            
            self.wfile.write( {'json': 
                json.dumps({"POST", request_id, parsed_path})
            })

        def do_HEAD(self):
            self._set_headers()
        


    def run(server_class=HTTPServer, handler_class=S, port=port):
        server_address = ('', port)
        httpd = server_class(server_address, handler_class)
        print 'Starting httpd...'
        print ' ', server_address
        
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
    startServer()

if __name__ == "__main__":
    run()