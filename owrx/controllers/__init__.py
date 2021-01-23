from datetime import datetime, timezone


class Controller(object):
    def __init__(self, handler, request, options):
        self.handler = handler
        self.request = request
        self.options = options

    def send_response(
        self, content, code=200, content_type="text/html", last_modified: datetime = None, max_age=None, headers=None
    ):
        self.handler.send_response(code)
        if headers is None:
            headers = {}
        if content_type is not None:
            headers["Content-Type"] = content_type
        if last_modified is not None:
            headers["Last-Modified"] = last_modified.astimezone(tz=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        if max_age is not None:
            headers["Cache-Control"] = "max-age={0}".format(max_age)
        for key, value in headers.items():
            self.handler.send_header(key, value)
        self.handler.end_headers()
        if type(content) == str:
            content = content.encode()
        self.handler.wfile.write(content)

    def send_redirect(self, location, code=303, cookies=None):
        self.handler.send_response(code)
        if cookies is not None:
            self.handler.send_header("Set-Cookie", cookies.output(header=""))
        self.handler.send_header("Location", location)
        self.handler.end_headers()

    def get_body(self):
        if "Content-Length" not in self.handler.headers:
            return None
        length = int(self.handler.headers["Content-Length"])
        return self.handler.rfile.read(length)

    def handle_request(self):
        action = "indexAction"
        if "action" in self.options:
            action = self.options["action"]
        getattr(self, action)()
