from abc import ABC, abstractmethod
from datetime import datetime


class Controller(ABC):
    def __init__(self, handler, request):
        self.handler = handler
        self.request = request

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

    @abstractmethod
    def handle_request(self):
        pass
