import base64
import hashlib
import json

class WebSocketConnection(object):
    def __init__(self, handler, messageHandler):
        self.handler = handler
        self.messageHandler = messageHandler
        my_headers = self.handler.headers.items()
        my_header_keys = list(map(lambda x:x[0],my_headers))
        h_key_exists = lambda x:my_header_keys.count(x)
        h_value = lambda x:my_headers[my_header_keys.index(x)][1]
        if (not h_key_exists("Upgrade")) or not (h_value("Upgrade")=="websocket") or (not h_key_exists("Sec-WebSocket-Key")):
            raise WebSocketException
        ws_key = h_value("Sec-WebSocket-Key")
        shakey = hashlib.sha1()
        shakey.update("{ws_key}258EAFA5-E914-47DA-95CA-C5AB0DC85B11".format(ws_key = ws_key).encode())
        ws_key_toreturn = base64.b64encode(shakey.digest())
        self.handler.wfile.write("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: {0}\r\nCQ-CQ-de: HA5KFU\r\n\r\n".format(ws_key_toreturn.decode()).encode())

    def get_header(self, size, opcode):
        ws_first_byte = 0b10000000 | (opcode & 0x0F)
        if (size > 125):
            return bytes([ws_first_byte, 126, (size>>8) & 0xff, size & 0xff])
        else:
            # 256 bytes binary message in a single unmasked frame
            return bytes([ws_first_byte, size])

    def send(self, data):
        # convenience
        if (type(data) == dict):
            data = json.dumps(data)

        # string-type messages are sent as text frames
        if (type(data) == str):
            header = self.get_header(len(data), 1)
            self.handler.wfile.write(header + data.encode('utf-8'))
            self.handler.wfile.flush()
        # anything else as binary
        else:
            header = self.get_header(len(data), 2)
            self.handler.wfile.write(header + data)
            self.handler.wfile.flush()

    def read_loop(self):
        open = True
        while (open):
            header = self.handler.rfile.read(2)
            opcode = header[0] & 0x0F
            length = header[1] & 0x7F
            mask = (header[1] & 0x80) >> 7
            if (length == 126):
                header = self.handler.rfile.read(2)
                length = (header[0] << 8) + header[1]
            if (mask):
                masking_key = self.handler.rfile.read(4)
            data = self.handler.rfile.read(length)
            if (mask):
                data = bytes([b ^ masking_key[index % 4] for (index, b) in enumerate(data)])
            if (opcode == 1):
                message = data.decode('utf-8')
                self.messageHandler.handleTextMessage(self, message)
            elif (opcode == 2):
                self.messageHandler.handleBinaryMessage(self, data)
            elif (opcode == 8):
                open = False
                self.messageHandler.handleClose(self)
            else:
                print("unsupported opcode: {0}".format(opcode))

class WebSocketException(Exception):
    pass
