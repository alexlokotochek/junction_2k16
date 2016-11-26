from visual import *
import vpykinect
import time
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import threading

skeleton = vpykinect.Skeleton(frame(visible=False))
skeleton.frame.visible = False

log = "{\n"

class HttpProcessor(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('content-type','application/json')
        self.end_headers()
        self.wfile.write(log + "}")

serv = HTTPServer(("localhost",80),HttpProcessor)
server = threading.Thread(target=serv.serve_forever)
server.start()

def log_skeleton(joints):
    global log
    log += '    "' + str(time.time()) + ': {\n'
    for i in range(0, len(joints)):
        log += '        "' + str(i) + '": "' + str(joints[i].x) + ", " + str(joints[i].y) + ", " + str(joints[i].z) + '"\n'
    log += "    },\n"
        
while True:
    rate(10)
    skeleton.frame.visible = skeleton.update()
    if skeleton.frame.visible:
        log_skeleton(skeleton.joints)