import base64
import hashlib
import json

class WebSocketConnection(object):
    def __init__(self, handler):
        self.handler = handler
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
        if(size>125):
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
            self.handler.wfile.write(header)
            self.handler.wfile.write(data.encode('utf-8'))
            self.handler.wfile.flush()
        # anything else as binary
        else:
            header = self.get_header(len(data), 2)
            self.handler.wfile.write(header)
            self.handler.wfile.write(data.encode())
            self.handler.wfile.flush()

class WebSocketException(Exception):
    pass
