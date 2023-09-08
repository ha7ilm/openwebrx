from pycsdr.modules import ExecModule
from pycsdr.types import Format
from owrx.aeronautical import AcarsProcessor
from owrx.map import Map
from owrx.aeronautical import AirplaneLocation, IcaoSource

import logging

logger = logging.getLogger(__name__)


class DumpVDL2Module(ExecModule):
    def __init__(self):
        super().__init__(
            Format.COMPLEX_SHORT,
            Format.CHAR,
            [
                "dumpvdl2",
                "--iq-file", "-",
                "--oversample", "1",
                "--sample-format", "S16_LE",
                "--output", "decoded:json:file:path=-",
            ]
        )


class VDL2MessageParser(AcarsProcessor):
    def __init__(self):
        super().__init__("VDL2")

    def process(self, line):
        msg = super().process(line)
        if msg is not None:
            try:
                payload = msg["vdl2"]
                if "avlc" in payload:
                    avlc = payload["avlc"]
                    src = avlc["src"]["addr"]
                    if avlc["frame_type"] == "I":
                        if "acars" in avlc:
                            self.processAcars(avlc["acars"])
                        elif "x25" in avlc:
                            x25 = avlc["x25"]
                            if "clnp" in x25:
                                clnp = x25["clnp"]
                                if "cotp" in clnp:
                                    cotp = clnp["cotp"]
                                    if "adsc_v2" in cotp:
                                        adsc_v2 = cotp["adsc_v2"]
                                        if "adsc_report" in adsc_v2:
                                            adsc_report = adsc_v2["adsc_report"]
                                            if "periodic_report" in adsc_report["data"]:
                                                periodic_report = adsc_report["data"]["periodic_report"]
                                                report_data = periodic_report["report_data"]
                                                self.processReport(report_data, src)
            except Exception:
                logger.exception("error processing VDL2 data")
        return msg

    def processReport(self, report, icao):
        if "position" not in report:
            return
        msg = {
            "lat": self.convertLatitude(**report["position"]["lat"]),
            "lon": self.convertLongitude(**report["position"]["lon"]),
            "altitude": report["position"]["alt"]["val"],
        }
        if "ground_vector" in report:
            msg.update({
                "groundtrack": report["ground_vector"]["ground_track"]["val"],
                "groundspeed": report["ground_vector"]["ground_speed"]["val"],
            })
        if "air_vector" in report:
            msg.update({
                "verticalspeed": report["air_vector"]["vertical_rate"]["val"],
            })
        Map.getSharedInstance().updateLocation(IcaoSource(icao), AirplaneLocation(msg), "VDL2")

    def convertLatitude(self, dir, **args) -> float:
        coord = self.convertCoordinate(**args)
        if dir == "south":
            coord *= -1
        return coord

    def convertLongitude(self, dir, **args) -> float:
        coord = self.convertCoordinate(**args)
        if dir == "west":
            coord *= -1
        return coord

    def convertCoordinate(self, deg, min, sec) -> float:
        return deg + float(min) / 60 + float(sec) / 3600
