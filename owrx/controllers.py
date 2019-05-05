import mimetypes
from owrx.websocket import WebSocketConnection
from owrx.config import PropertyManager
from owrx.source import SpectrumThread, DspManager, CpuUsageThread
import json

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

class SpectrumForwarder(object):
    def __init__(self, conn):
        self.conn = conn
    def write_spectrum_data(self, data):
        self.conn.send(bytes([0x01]) + data)
    def write_dsp_data(self, data):
        self.conn.send(bytes([0x02]) + data)
    def write_s_meter_level(self, level):
        self.conn.send({"type":"smeter","value":level})
    def write_cpu_usage(self, usage):
        self.conn.send({"type":"cpuusage","value":usage})

class WebSocketMessageHandler(object):
    def __init__(self):
        self.handshake = None
        self.forwarder = None

    def handleTextMessage(self, conn, message):
        if (message[:16] == "SERVER DE CLIENT"):
            # maybe put some more info in there? nothing to store yet.
            self.handshake = "completed"

            config = {}
            pm = PropertyManager.getSharedInstance()

            for key in ["waterfall_colors", "waterfall_min_level", "waterfall_max_level", "waterfall_auto_level_margin",
                        "shown_center_freq", "samp_rate", "fft_size", "fft_fps", "audio_compression", "fft_compression",
                        "max_clients", "start_mod", "client_audio_buffer_size"]:

                config[key] = pm.getPropertyValue(key)

            config["start_offset_freq"] = pm.getPropertyValue("start_freq") - pm.getPropertyValue("center_freq")

            conn.send({"type":"config","value":config})
            print("client connection intitialized")

            receiver_details = dict((key, pm.getPropertyValue(key)) for key in ["receiver_name", "receiver_location",
                                                                                "receiver_qra", "receiver_asl",
                                                                                "receiver_gps", "photo_title",
                                                                                "photo_desc"]
                                    )
            conn.send({"type":"receiver_details","value":receiver_details})

            self.forwarder = SpectrumForwarder(conn)
            SpectrumThread.getSharedInstance().add_client(self.forwarder)
            CpuUsageThread.getSharedInstance().add_client(self.forwarder)

            self.dsp = DspManager(self.forwarder)

            return

        if not self.handshake:
            print("not answering client request since handshake is not complete")
            return

        try:
            message = json.loads(message)
            if message["type"] == "dspcontrol":
                if "params" in message:
                    params = message["params"]
                    for key, value in params.items():
                        self.dsp.setProperty(key, value)

                if "action" in message and message["action"] == "start":
                    self.dsp.start()
        except json.JSONDecodeError:
            print("message is not json: {0}".format(message))

    def handleBinaryMessage(self, conn, data):
        print("unsupported binary message, discarding")

    def handleClose(self, conn):
        if self.forwarder:
            SpectrumThread.getSharedInstance().remove_client(self.forwarder)
            CpuUsageThread.getSharedInstance().remove_client(self.forwarder)
        if self.dsp:
            self.dsp.stop()

class WebSocketController(Controller):
    def handle_request(self):
        conn = WebSocketConnection(self.handler, WebSocketMessageHandler())
        conn.send("CLIENT DE SERVER openwebrx.py")
        # enter read loop
        conn.read_loop()
