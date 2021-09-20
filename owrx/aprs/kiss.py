from pycsdr.types import Format
from csdr.module import ThreadModule
import pickle

import logging

logger = logging.getLogger(__name__)

FEND = 0xC0
FESC = 0xDB
TFEND = 0xDC
TFESC = 0xDD


class KissDeframer(ThreadModule):
    def __init__(self):
        self.escaped = False
        self.buf = bytearray()
        super().__init__()

    def getInputFormat(self) -> Format:
        return Format.CHAR

    def getOutputFormat(self) -> Format:
        return Format.CHAR

    def run(self):
        while self.doRun:
            data = self.reader.read()
            if data is None:
                self.doRun = False
            else:
                for frame in self.parse(data):
                    self.writer.write(pickle.dumps(frame))

    def parse(self, input):
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
            elif b == FEND:
                # data frames start with 0x00
                if len(self.buf) > 1 and self.buf[0] == 0x00:
                    yield self.buf[1:]
                self.buf = bytearray()
            else:
                self.buf.append(b)
