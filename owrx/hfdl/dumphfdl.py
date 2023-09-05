from pycsdr.modules import ExecModule
from pycsdr.types import Format
from csdr.module import JsonParser
from owrx.adsb.modes import AirplaneLocation
from owrx.map import Map
from datetime import timedelta


class HfdlAirplaneLocation(AirplaneLocation):
    def __init__(self, message):
        super().__init__(None, message)

    def getTTL(self) -> timedelta:
        return timedelta(minutes=60)


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
            ]
        )


class HFDLMessageParser(JsonParser):
    def __init__(self):
        super().__init__("HFDL")

    def process(self, line):
        msg = super().process(line)
        if msg is not None:
            payload = msg["hfdl"]
            if "lpdu" in payload:
                lpdu = payload["lpdu"]
                if lpdu["type"]["id"] in [13, 29]:
                    hfnpdu = lpdu["hfnpdu"]
                    if hfnpdu["type"]["id"] == 209:
                        if "pos" in hfnpdu:
                            pos = hfnpdu['pos']
                            if abs(pos['lat']) <= 90 and abs(pos['lon']) <= 180:
                                Map.getSharedInstance().updateLocation({"flight": hfnpdu["flight_id"]}, HfdlAirplaneLocation(pos), "HFDL")
        return msg
