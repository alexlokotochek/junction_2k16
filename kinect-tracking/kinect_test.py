from visual import *
import vpykinect
import time
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import threading

skeleton = vpykinect.Skeleton(frame(visible=False))
skeleton.frame.visible = False

log = "{\n"
points = []

class HttpProcessor(BaseHTTPRequestHandler):
    global last_point
    def do_GET(self):
        print self.path
        self.send_response(200)
        self.send_header('content-type','application/json')
        self.end_headers()
        if (self.path == "/all_data"):
            self.wfile.write(log + "}")
        elif (self.path == "/last_point"):
            self.wfile.write(str(points[-1][0]) + ", " + str(points[-1][1]) + ", " + str(points[-1][2]))
        elif (self.path == "/all_points"):
            response = ""
            for point in points:
                response += str(point) + "\n"
            self.wfile.write(response)
        else:
            self.wfile.write("Use /all_data to get all collected information\nUse /all_points to get all path points recorded for one customer (we currently track just one skeleton for testing purposes)\nUse /last_point to get last path point")

serv = HTTPServer(("85.188.11.77",12358),HttpProcessor)
server = threading.Thread(target=serv.serve_forever)
server.start()

def log_skeleton(joints):
    global log, last_point
    log += '    "' + str(time.time()) + ': {\n'
    for i in range(0, len(joints)):
        log += '        "' + str(i) + '": "' + str(joints[i].x) + ", " + str(joints[i].y) + ", " + str(joints[i].z) + '"\n'
    points.append((joints[3].x, joints[3].y, joints[3].z))
    print points[-1]
    log += "    },\n"
        
while True:
    rate(10)
    skeleton.frame.visible = skeleton.update()
    if skeleton.frame.visible:
        log_skeleton(skeleton.joints)