import mimetypes
from owrx.websocket import WebSocketConnection
from owrx.config import PropertyManager
from owrx.source import SpectrumThread, DspManager, CpuUsageThread, SdrService
import json
import os
from datetime import datetime

class Controller(object):
    def __init__(self, handler, matches):
        self.handler = handler
        self.matches = matches
    def send_response(self, content, code = 200, content_type = "text/html", last_modified: datetime = None, max_age = None):
        self.handler.send_response(code)
        if content_type is not None:
            self.handler.send_header("Content-Type", content_type)
        if last_modified is not None:
            self.handler.send_header("Last-Modified", last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT"))
        if max_age is not None:
            self.handler.send_header("Cache-Control", "max-age: {0}".format(max_age))
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

class AssetsController(Controller):
    def serve_file(self, file, content_type = None):
        try:
            modified = datetime.fromtimestamp(os.path.getmtime('htdocs/' + file))

            if "If-Modified-Since" in self.handler.headers:
                client_modified = datetime.strptime(self.handler.headers["If-Modified-Since"], "%a, %d %b %Y %H:%M:%S %Z")
                if modified <= client_modified:
                    self.send_response("", code = 304)
                    return

            f = open('htdocs/' + file, 'rb')
            data = f.read()
            f.close()

            if content_type is None:
                (content_type, encoding) = mimetypes.MimeTypes().guess_type(file)
            self.send_response(data, content_type = content_type, last_modified = modified, max_age = 3600)
        except FileNotFoundError:
            self.send_response("file not found", code = 404)
    def handle_request(self):
        filename = self.matches.group(1)
        self.serve_file(filename)

class IndexController(AssetsController):
    def handle_request(self):
        self.serve_file("index.wrx", "text/html")

class OpenWebRxClient(object):
    config_keys = ["waterfall_colors", "waterfall_min_level", "waterfall_max_level",
                   "waterfall_auto_level_margin", "lfo_offset", "samp_rate", "fft_size", "fft_fps",
                   "audio_compression", "fft_compression", "max_clients", "start_mod",
                   "client_audio_buffer_size", "start_freq", "center_freq"]
    def __init__(self, conn):
        self.conn = conn

        self.dsp = None
        self.sdr = None
        self.configProps = None

        pm = PropertyManager.getSharedInstance()

        self.setSdr()

        # send receiver info
        receiver_keys = ["receiver_name", "receiver_location", "receiver_qra", "receiver_asl",  "receiver_gps",
                         "photo_title", "photo_desc"]
        receiver_details = dict((key, pm.getPropertyValue(key)) for key in receiver_keys)
        self.write_receiver_details(receiver_details)

        CpuUsageThread.getSharedInstance().add_client(self)

    def sendConfig(self, key, value):
        config = dict((key, self.configProps[key]) for key in OpenWebRxClient.config_keys)
        # TODO mathematical properties? hmmmm
        config["start_offset_freq"] = self.configProps["start_freq"] - self.configProps["center_freq"]
        self.write_config(config)
    def setSdr(self, id = None):
        self.stopDsp()

        if self.configProps is not None:
            self.configProps.unwire(self.sendConfig)

        self.sdr = SdrService.getSource(id)

        # send initial config
        self.configProps = self.sdr.getProps().collect(*OpenWebRxClient.config_keys).defaults(PropertyManager.getSharedInstance())

        self.configProps.wire(self.sendConfig)
        self.sendConfig(None, None)

        self.sdr.getSpectrumThread().add_client(self)

    def startDsp(self):
        if self.dsp is None:
            self.dsp = DspManager(self, self.sdr)
            self.dsp.start()

    def stopDsp(self):
        if self.dsp is not None:
            self.dsp.stop()
            self.dsp = None
        if self.sdr is not None:
            self.sdr.spectrumThread.remove_client(self)
        # TODO: this should be disabled somehow, just not with the dsp
        #CpuUsageThread.getSharedInstance().remove_client(self)

    def setParams(self, params):
        # only the keys in the protected property manager can be overridden from the web
        protected = self.sdr.getProps().collect("samp_rate", "center_freq", "rf_gain", "type") \
            .defaults(PropertyManager.getSharedInstance())
        for key, value in params.items():
            protected[key] = value

    def setDspProperties(self, params):
        for key, value in params.items():
            self.dsp.setProperty(key, value)

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
        self.dsp = None

    def handleTextMessage(self, conn, message):
        if (message[:16] == "SERVER DE CLIENT"):
            # maybe put some more info in there? nothing to store yet.
            self.handshake = "completed"
            print("client connection intitialized")

            self.client = OpenWebRxClient(conn)

            return

        if not self.handshake:
            print("not answering client request since handshake is not complete")
            return

        try:
            message = json.loads(message)
            if "type" in message:
                if message["type"] == "dspcontrol":
                    if "action" in message and message["action"] == "start":
                        self.client.startDsp()

                    if "params" in message:
                        params = message["params"]
                        self.client.setDspProperties(params)

                if message["type"] == "config":
                    if "params" in message:
                        self.client.setParams(message["params"])
                if message["type"] == "setsdr":
                    if "params" in message:
                        self.client.setSdr(message["params"]["sdr"])
            else:
                print("received message without type: {0}".format(message))

        except json.JSONDecodeError:
            print("message is not json: {0}".format(message))

    def handleBinaryMessage(self, conn, data):
        print("unsupported binary message, discarding")

    def handleClose(self, conn):
        if self.client:
            self.client.stopDsp()

class WebSocketController(Controller):
    def handle_request(self):
        conn = WebSocketConnection(self.handler, WebSocketMessageHandler())
        conn.send("CLIENT DE SERVER openwebrx.py")
        # enter read loop
        conn.read_loop()
