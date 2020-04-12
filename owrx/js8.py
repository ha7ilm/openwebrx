from .wsjt import WsjtChopper
from .parser import Parser
import re

import logging

logger = logging.getLogger(__name__)


class Js8Chopper(WsjtChopper):
    def getInterval(self):
        return 15

    def getFileTimestampFormat(self):
        return "%y%m%d_%H%M%S"

    def decoder_commandline(self, file):
        return ["js8", "--js8", "-d", str(self.decoding_depth("js8")), file]


class Js8Parser(Parser):
    decoderRegex = re.compile(" ?<Decode(Started|Debug|Finished)>")

    def parse(self, raw):
        freq, raw_msg = raw
        self.setDialFrequency(freq)
        msg = raw_msg.decode().rstrip()
        if Js8Parser.decoderRegex.match(msg):
            return
        if msg.startswith(" EOF on input file"):
            return
        logger.debug(msg)
