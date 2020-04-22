from .audio import AudioChopperProfile
from .parser import Parser
import re
from js8py import Js8
from js8py.frames import Js8FrameHeartbeat, Js8FrameCompound
from owrx.map import Map, LocatorLocation
from owrx.pskreporter import PskReporter
from owrx.metrics import Metrics, CounterMetric

import logging

logger = logging.getLogger(__name__)


class Js8NormalProfile(AudioChopperProfile):
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
            self.handler.write_js8_message(frame, self.dial_freq)
            logger.debug(frame)

            self.pushDecode()

            if (isinstance(frame, Js8FrameHeartbeat) or isinstance(frame, Js8FrameCompound)) and frame.grid:
                Map.getSharedInstance().updateLocation(
                    frame.callsign, LocatorLocation(frame.grid), "JS8", self.band
                )
                PskReporter.getSharedInstance().spot({
                    "callsign": frame.callsign,
                    "mode": "JS8",
                    "locator": frame.grid,
                    "freq": self.dial_freq + frame.freq,
                    "db": frame.db,
                    "timestamp": frame.timestamp,
                    "msg": str(frame)
                })

        except Exception:
            logger.exception("error while parsing js8 message")

    def pushDecode(self):
        metrics = Metrics.getSharedInstance()
        band = "unknown"
        if self.band is not None:
            band = self.band.getName()
        if band is None:
            band = "unknown"

        name = "js8call.decodes.{band}.JS8".format(band=band)
        metric = metrics.getMetric(name)
        if metric is None:
            metric = CounterMetric()
            metrics.addMetric(name, metric)

        metric.inc()
