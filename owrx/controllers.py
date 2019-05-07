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

class OpenWebRxClient(object):
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
    def write_secondary_fft(self, data):
        self.conn.send(bytes([0x03]) + data)
    def write_secondary_demod(self, data):
        self.conn.send(bytes([0x04]) + data)
    def write_secondary_dsp_config(self, cfg):
        self.conn.send({"type":"secondary_config", "value":cfg})
    def write_config(self, cfg):
        self.conn.send({"type":"config","value":cfg})
    def write_receiver_details(self, details):
        self.conn.send({"type":"receiver_details","value":details})

class WebSocketMessageHandler(object):
    def __init__(self):
        self.handshake = None
        self.client = None

    def handleTextMessage(self, conn, message):
        pm = PropertyManager.getSharedInstance()

        if (message[:16] == "SERVER DE CLIENT"):
            # maybe put some more info in there? nothing to store yet.
            self.handshake = "completed"

            self.client = OpenWebRxClient(conn)

            config_keys = ["waterfall_colors", "waterfall_min_level", "waterfall_max_level",
                           "waterfall_auto_level_margin", "shown_center_freq", "samp_rate", "fft_size", "fft_fps",
                           "audio_compression", "fft_compression", "max_clients", "start_mod",
                           "client_audio_buffer_size"]
            config = dict((key, pm.getPropertyValue(key)) for key in config_keys)
            config["start_offset_freq"] = pm.getPropertyValue("start_freq") - pm.getPropertyValue("center_freq")
            self.client.write_config(config)
            print("client connection intitialized")

            receiver_keys = ["receiver_name", "receiver_location", "receiver_qra", "receiver_asl",  "receiver_gps",
                             "photo_title", "photo_desc"]
            receiver_details = dict((key, pm.getPropertyValue(key)) for key in receiver_keys)
            self.client.write_receiver_details(receiver_details)

            SpectrumThread.getSharedInstance().add_client(self.client)
            CpuUsageThread.getSharedInstance().add_client(self.client)

            self.dsp = DspManager(self.client)

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

            if message["type"] == "config":
                for key, value in message["params"].items():
                    # only the keys in the protected property manager can be overridden from the web
                    protected = pm.collect("samp_rate", "center_freq", "rf_gain")
                    protected[key] = value

        except json.JSONDecodeError:
            print("message is not json: {0}".format(message))

    def handleBinaryMessage(self, conn, data):
        print("unsupported binary message, discarding")

    def handleClose(self, conn):
        if self.client:
            SpectrumThread.getSharedInstance().remove_client(self.client)
            CpuUsageThread.getSharedInstance().remove_client(self.client)
        if self.dsp:
            self.dsp.stop()

class WebSocketController(Controller):
    def handle_request(self):
        conn = WebSocketConnection(self.handler, WebSocketMessageHandler())
        conn.send("CLIENT DE SERVER openwebrx.py")
        # enter read loop
        conn.read_loop()
