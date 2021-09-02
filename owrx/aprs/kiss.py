import socket
import time

import logging

logger = logging.getLogger(__name__)

FEND = 0xC0
FESC = 0xDB
TFEND = 0xDC
TFESC = 0xDD


class KissClient(object):
    def __init__(self, port):
        delay = 0.5
        retries = 0
        while True:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect(("localhost", port))
                break
            except ConnectionError:
                if retries > 20:
                    logger.error("maximum number of connection attempts reached. did direwolf start up correctly?")
                    raise
                retries += 1
            time.sleep(delay)

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
