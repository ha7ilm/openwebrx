from owrx.controllers import StatusController, IndexController, AssetsController
from http.server import BaseHTTPRequestHandler
import re

class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        self.router = Router()
        super().__init__(request, client_address, server)
    def do_GET(self):
        self.router.route(self)

class Router(object):
    mappings = [
        {"route": "/", "controller": IndexController},
        {"route": "/status", "controller": StatusController},
        {"regex": "/static/(.+)", "controller": AssetsController}
    ]
    def find_controller(self, path):
        for m in Router.mappings:
            if "route" in m:
                if m["route"] == path:
                    return (m["controller"], None)
            if "regex" in m:
                regex = re.compile(m["regex"])
                matches = regex.match(path)
                if matches:
                    return (m["controller"], matches)
    def route(self, handler):
        res = self.find_controller(handler.path)
        #print("path: {0}, controller: {1}, matches: {2}".format(handler.path, controller, matches))
        if res is not None:
            (controller, matches) = res
            controller(handler, matches).handle_request()
        else:
            handler.send_error(404, "Not Found", "The page you requested could not be found.")
