import mimetypes
from owrx.websocket import WebSocketConnection
from owrx.config import PropertyManager

class Controller(object):
    def __init__(self, handler, matches):
        self.handler = handler
        self.matches = matches
    def send_response(self, content, code = 200, content_type = "text/html"):
        self.handler.send_response(code)
        if content_type is not None:
            self.handler.send_header("Content-Type", content_type)
        self.handler.end_headers()
        if (type(content) == str):
            content = content.encode()
        self.handler.wfile.write(content)
    def render_template(self, template, **variables):
        f = open('htdocs/' + template)
        data = f.read()
        f.close()

        self.send_response(data)

class StatusController(Controller):
    def handle_request(self):
        self.send_response("you have reached the status page!")

class IndexController(Controller):
    def handle_request(self):
        self.render_template("index.wrx")

class AssetsController(Controller):
    def serve_file(self, file):
        try:
            f = open('htdocs/' + file, 'rb')
            data = f.read()
            f.close()

            (content_type, encoding) = mimetypes.MimeTypes().guess_type(file)
            self.send_response(data, content_type = content_type)
        except FileNotFoundError:
            self.send_response("file not found", code = 404)
    def handle_request(self):
        filename = self.matches.group(1)
        self.serve_file(filename)


class WebSocketController(Controller):
    def handle_request(self):
        conn = WebSocketConnection(self.handler)
        conn.send("CLIENT DE SERVER openwebrx.py")

        config = {}
        pm = PropertyManager.getSharedInstance()

        for key in ["waterfall_colors", "waterfall_min_level", "waterfall_max_level", "waterfall_auto_level_margin",
                    "shown_center_freq", "samp_rate", "fft_size", "fft_fps", "audio_compression", "fft_compression",
                    "max_clients"]:

            config[key] = pm.getProperty(key).getValue()

        conn.send({"type":"config","value":config})
