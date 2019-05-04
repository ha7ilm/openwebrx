import mimetypes
from owrx.websocket import WebSocketConnection
from owrx.config import PropertyManager
from owrx.source import SpectrumThread
import csdr
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

class WebSocketMessageHandler(object):
    def __init__(self):
        self.forwarder = None

    def handleTextMessage(self, conn, message):
        if (message[:16] == "SERVER DE CLIENT"):
            config = {}
            pm = PropertyManager.getSharedInstance()

            for key in ["waterfall_colors", "waterfall_min_level", "waterfall_max_level", "waterfall_auto_level_margin",
                        "shown_center_freq", "samp_rate", "fft_size", "fft_fps", "audio_compression", "fft_compression",
                        "max_clients", "start_mod"]:

                config[key] = pm.getPropertyValue(key)

            config["start_offset_freq"] = pm.getPropertyValue("start_freq") - pm.getPropertyValue("center_freq")

            conn.send({"type":"config","value":config})
            print("client connection intitialized")

            dsp = self.dsp = csdr.dsp()
            dsp_initialized=False
            dsp.set_audio_compression(pm.getPropertyValue("audio_compression"))
            dsp.set_fft_compression(pm.getPropertyValue("fft_compression")) #used by secondary chains
            dsp.set_format_conversion(pm.getPropertyValue("format_conversion"))
            dsp.set_offset_freq(0)
            dsp.set_bpf(-4000,4000)
            dsp.set_secondary_fft_size(pm.getPropertyValue("digimodes_fft_size"))
            dsp.nc_port=pm.getPropertyValue("iq_server_port")
            dsp.csdr_dynamic_bufsize = pm.getPropertyValue("csdr_dynamic_bufsize")
            dsp.csdr_print_bufsizes = pm.getPropertyValue("csdr_print_bufsizes")
            dsp.csdr_through = pm.getPropertyValue("csdr_through")
            do_secondary_demod=False

            self.forwarder = SpectrumForwarder(conn)
            SpectrumThread.getSharedInstance().add_client(self.forwarder)

        else:
            try:
                message = json.loads(message)
                if message["type"] == "start":
                    self.dsp.set_samp_rate(message["params"]["output_rate"])
                    self.dsp.start()
            except json.JSONDecodeError:
                print("message is not json: {0}".format(message))

    def handleBinaryMessage(self, conn, data):
        print("unsupported binary message, discarding")

    def handleClose(self, conn):
        if self.forwarder:
            SpectrumThread.getSharedInstance().remove_client(self.forwarder)

class WebSocketController(Controller):
    def handle_request(self):
        conn = WebSocketConnection(self.handler, WebSocketMessageHandler())
        conn.send("CLIENT DE SERVER openwebrx.py")
        # enter read loop
        conn.read_loop()
