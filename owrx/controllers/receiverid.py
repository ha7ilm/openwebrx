from owrx.controllers import Controller
from owrx.receiverid import ReceiverId
from datetime import datetime


class ReceiverIdController(Controller):
    def __init__(self, handler, request, options):
        super().__init__(handler, request, options)
        self.authHeader = None

    def send_response(
        self, content, code=200, content_type="text/html", last_modified: datetime = None, max_age=None, headers=None
    ):
        if self.authHeader is not None:
            if headers is None:
                headers = {}
            headers["Authorization"] = self.authHeader
        super().send_response(
            content, code=code, content_type=content_type, last_modified=last_modified, max_age=max_age, headers=headers
        )
        pass

    def handle_request(self):
        if "Authorization" in self.request.headers:
            self.authHeader = ReceiverId.getResponseHeader(self.request.headers["Authorization"])
        super().handle_request()
