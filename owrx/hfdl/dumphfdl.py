from pycsdr.modules import ExecModule
from pycsdr.types import Format
from owrx.aeronautical import AirplaneLocation, AcarsProcessor, IcaoSource, FlightSource
from owrx.map import Map
from owrx.metrics import Metrics, CounterMetric
from owrx.reporting import ReportingEngine
from datetime import datetime, timezone, timedelta

import logging

logger = logging.getLogger(__name__)


class DumpHFDLModule(ExecModule):
    def __init__(self):
        super().__init__(
            Format.COMPLEX_FLOAT,
            Format.CHAR,
            [
                "dumphfdl",
                "--iq-file", "-",
                "--sample-format", "CF32",
                "--sample-rate", "12000",
                "--output", "decoded:json:file:path=-",
                "0",
            ],
            flushSize=50000,
        )


class HFDLMessageParser(AcarsProcessor):
    def __init__(self):
        name = "dumphfdl.decodes.hfdl"
        self.metrics = Metrics.getSharedInstance().getMetric(name)
        if self.metrics is None:
            self.metrics = CounterMetric()
            Metrics.getSharedInstance().addMetric(name, self.metrics)
        super().__init__("HFDL")

    def process(self, line):
        msg = super().process(line)
        if msg is not None:
            try:
                payload = msg["hfdl"]
                if "lpdu" in payload:
                    lpdu = payload["lpdu"]
                    icao = lpdu["src"]["ac_info"]["icao"] if "ac_info" in lpdu["src"] else None
                    if lpdu["type"]["id"] in [13, 29]:
                        hfnpdu = lpdu["hfnpdu"]
                        if hfnpdu["type"]["id"] == 209:
                            # performance data
                            self.processPosition(hfnpdu, icao)
                        elif hfnpdu["type"]["id"] == 255:
                            # enveloped data
                            if "acars" in hfnpdu:
                                self.processAcars(hfnpdu["acars"], icao)
                    elif lpdu["type"]["id"] in [79, 143, 191]:
                        if "ac_info" in lpdu:
                            icao = lpdu["ac_info"]["icao"]
                        self.processPosition(lpdu["hfnpdu"], icao)
            except Exception:
                logger.exception("error processing HFDL data")

            self.metrics.inc()

        ReportingEngine.getSharedInstance().spot(msg)
        return msg

    def processPosition(self, hfnpdu, icao=None):
        if "pos" in hfnpdu:
            pos = hfnpdu["pos"]
            if abs(pos['lat']) <= 90 and abs(pos['lon']) <= 180:
                flight = self.processFlight(hfnpdu["flight_id"])
                
                if icao is not None:
                    source = IcaoSource(icao, flight=flight)
                elif flight:
                    source = FlightSource(flight)
                else:
                    source = None

                if source:
                    msg = {
                        "lat": pos["lat"],
                        "lon": pos["lon"],
                        "flight": flight
                    }
                    if "utc_time" in hfnpdu:
                        ts = self.processTimestamp(**hfnpdu["utc_time"])
                    elif "time" in hfnpdu:
                        ts = self.processTimestamp(**hfnpdu["time"])
                    else:
                        ts = None
                    Map.getSharedInstance().updateLocation(source, AirplaneLocation(msg), "HFDL", timestamp=ts)

    def processTimestamp(self, hour, min, sec) -> datetime:
        now = datetime.now(timezone.utc)
        t = now.replace(hour=hour, minute=min, second=sec, microsecond=0)
        # if we have moved the time to the future, it's most likely that we're close to midnight and the time
        # we received actually refers to yesterday
        if t > now:
            t -= timedelta(days=1)
        return t
