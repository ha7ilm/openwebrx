from owrx.audio import AudioChopperProfile, ConfigWiredProfileSource
from owrx.audio.chopper import AudioChopperParser
import re
from js8py import Js8
from js8py.frames import Js8FrameHeartbeat, Js8FrameCompound
from owrx.map import Map, LocatorLocation
from owrx.metrics import Metrics, CounterMetric
from owrx.config import Config
from abc import ABCMeta, abstractmethod
from owrx.reporting import ReportingEngine
from owrx.bands import Bandplan
from typing import List

import logging

logger = logging.getLogger(__name__)


class Js8Profile(AudioChopperProfile, metaclass=ABCMeta):
    def decoding_depth(self):
        pm = Config.get()
        # return global default
        if "js8_decoding_depth" in pm:
            return pm["js8_decoding_depth"]
        # default when no setting is provided
        return 3

    def getFileTimestampFormat(self):
        return "%y%m%d_%H%M%S"

    def decoder_commandline(self, file):
        return ["js8", "--js8", "-b", self.get_sub_mode(), "-d", str(self.decoding_depth()), file]

    @abstractmethod
    def get_sub_mode(self):
        pass


class Js8ProfileSource(ConfigWiredProfileSource):
    def getPropertiesToWire(self) -> List[str]:
        return ["js8_enabled_profiles"]

    def getProfiles(self) -> List[AudioChopperProfile]:
        config = Config.get()
        profiles = config["js8_enabled_profiles"] if "js8_enabled_profiles" in config else []
        return [self._loadProfile(p) for p in profiles]

    def _loadProfile(self, profileName):
        className = "Js8{0}Profile".format(profileName[0].upper() + profileName[1:].lower())
        return globals()[className]()


class Js8NormalProfile(Js8Profile):
    def getInterval(self):
        return 15

    def get_sub_mode(self):
        return "A"


class Js8SlowProfile(Js8Profile):
    def getInterval(self):
        return 30

    def get_sub_mode(self):
        return "E"


class Js8FastProfile(Js8Profile):
    def getInterval(self):
        return 10

    def get_sub_mode(self):
        return "B"


class Js8TurboProfile(Js8Profile):
    def getInterval(self):
        return 6

    def get_sub_mode(self):
        return "C"


class Js8Parser(AudioChopperParser):
    decoderRegex = re.compile(" ?<Decode(Started|Debug|Finished)>")

    def parse(self, profile: AudioChopperProfile, freq: int, raw_msg: bytes):
        try:
            band = None
            if freq is not None:
                band = Bandplan.getSharedInstance().findBand(freq)

            msg = raw_msg.decode().rstrip()
            if Js8Parser.decoderRegex.match(msg):
                return
            if msg.startswith(" EOF on input file"):
                return

            frame = Js8().parse_message(msg)

            self.pushDecode(band)

            if (isinstance(frame, Js8FrameHeartbeat) or isinstance(frame, Js8FrameCompound)) and frame.grid:
                Map.getSharedInstance().updateLocation(
                    frame.callsign, LocatorLocation(frame.grid), "JS8", band
                )
                ReportingEngine.getSharedInstance().spot(
                    {
                        "callsign": frame.callsign,
                        "mode": "JS8",
                        "locator": frame.grid,
                        "freq": freq + frame.freq,
                        "db": frame.db,
                        "timestamp": frame.timestamp,
                        "msg": str(frame),
                    }
                )

            out = {
                "mode": "JS8",
                "msg": str(frame),
                "timestamp": frame.timestamp,
                "db": frame.db,
                "dt": frame.dt,
                "freq": freq + frame.freq,
                "thread_type": frame.thread_type,
                "js8mode": frame.mode,
            }

            return out

        except Exception:
            logger.exception("error while parsing js8 message")

    def pushDecode(self, band):
        metrics = Metrics.getSharedInstance()
        bandName = "unknown"
        if band is not None:
            bandName = band.getName()

        name = "js8call.decodes.{band}.JS8".format(band=bandName)
        metric = metrics.getMetric(name)
        if metric is None:
            metric = CounterMetric()
            metrics.addMetric(name, metric)

        metric.inc()
