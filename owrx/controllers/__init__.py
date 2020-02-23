from abc import ABC, abstractmethod
from datetime import datetime


class Controller(ABC):
    def __init__(self, handler, request, options):
        self.handler = handler
        self.request = request
        self.options = options

    def send_response(self, content, code=200, content_type="text/html", last_modified: datetime = None, max_age=None):
        self.handler.send_response(code)
        if content_type is not None:
            self.handler.send_header("Content-Type", content_type)
        if last_modified is not None:
            self.handler.send_header("Last-Modified", last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT"))
        if max_age is not None:
            self.handler.send_header("Cache-Control", "max-age: {0}".format(max_age))
        self.handler.end_headers()
        if type(content) == str:
            content = content.encode()
        self.handler.wfile.write(content)

    def send_redirect(self, location, code=303):
        self.handler.send_response(code)
        self.handler.send_header("Location", location)
        self.handler.end_headers()

    def handle_request(self):
        action = "indexAction"
        if "action" in self.options:
            action = self.options["action"]
        getattr(self, action)()
