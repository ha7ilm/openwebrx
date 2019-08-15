import socket
import time
import logging
import random

logger = logging.getLogger(__name__)

FEND = 0xC0
FESC = 0xDB
TFEND = 0xDC
TFESC = 0xDD


class KissClient(object):
    @staticmethod
    def getFreePort():
        # direwolf has some strange hardcoded port ranges
        while True:
            try:
                port = random.randrange(1024, 49151)
                # test if port is available for use
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(('localhost', port))
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.close()
                return port
            except OSError:
                pass

    def __init__(self, port):
        time.sleep(1)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(("localhost", port))

    def read(self):
        return self.socket.recv(1)


class KissDeframer(object):
    def __init__(self):
        self.escaped = False
        self.buf = bytearray()

    def parse(self, input):
        frames = []
        for b in input:
            if b == FESC:
                self.escaped = True
            elif self.escaped:
                if b == TFEND:
                    self.buf.append(FEND)
                elif b == TFESC:
                    self.buf.append(FESC)
                else:
                    logger.warning("invalid escape char: %s", str(input[0]))
                self.escaped = False
            elif input[0] == FEND:
                # data frames start with 0x00
                if len(self.buf) > 1 and self.buf[0] == 0x00:
                    frames += [self.buf[1:]]
                self.buf = bytearray()
            else:
                self.buf.append(b)
        return frames
