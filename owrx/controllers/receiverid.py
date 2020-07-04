from owrx.controllers import Controller
from owrx.receiverid import ReceiverId
from datetime import datetime


class ReceiverIdController(Controller):
    def __init__(self, handler, request, options):
        super().__init__(handler, request, options)
        self.authHeaders = []

    def send_response(self, content, code=200, content_type="text/html", last_modified: datetime = None, max_age=None, headers=None):
        if headers is None:
            headers = {}
        headers['Authorization'] = self.authHeaders
        super().send_response(content, code=code, content_type=content_type, last_modified=last_modified, max_age=max_age, headers=headers)
        pass

    def handle_request(self):
        headers = self.request.headers.get_all("Authorization", [])
        self.authHeaders = [ReceiverId.getResponseHeader(h) for h in headers]
        super().handle_request()
