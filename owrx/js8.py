from .wsjt import WsjtChopper
from .parser import Parser
import re
from js8py import Js8
from js8py.frames import Js8FrameDirected, Js8FrameData, Js8FrameDataCompressed

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
        try:
            freq, raw_msg = raw
            self.setDialFrequency(freq)
            msg = raw_msg.decode().rstrip()
            if Js8Parser.decoderRegex.match(msg):
                return
            if msg.startswith(" EOF on input file"):
                return

            logger.debug(msg)

            frame = Js8().parse_message(msg)
            if frame is None:
                logger.warning("message could not be parsed")
            elif isinstance(frame, Js8FrameDirected):
                logger.debug("directed frame from: {0} to: {1}".format(frame.callsign_from, frame.callsign_to))
            elif isinstance(frame, Js8FrameData) or isinstance(frame, Js8FrameDataCompressed):
                logger.debug("message frame: {0}".format(frame.message))

        except Exception:
            logger.exception("error while parsing js8 message")
