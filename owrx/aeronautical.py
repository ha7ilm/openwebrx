from owrx.map import Map, LatLngLocation, Source
from csdr.module import JsonParser
from abc import ABCMeta


class AirplaneLocation(LatLngLocation):
    def __init__(self, message):
        self.props = message
        if "lat" in message and "lon" in message:
            super().__init__(message["lat"], message["lon"])
        else:
            self.lat = None
            self.lon = None

    def __dict__(self):
        res = super().__dict__()
        res.update(self.props)
        return res


class IcaoSource(Source):
    def __init__(self, icao: str, humanReadable: str = None):
        self.icao = icao.upper()
        self.humanReadable = humanReadable

    def getKey(self) -> str:
        return "icao:{}".format(self.icao)

    def __dict__(self):
        d = {"icao": self.icao}
        if self.humanReadable is not None:
            d["humanReadable"] = self.humanReadable
        return d


class AcarsSource(Source):
    def __init__(self, flight):
        self.flight = flight

    def getKey(self) -> str:
        return "acars:{}".format(self.flight)

    def __dict__(self):
        return {"flight": self.flight}


class AcarsProcessor(JsonParser, metaclass=ABCMeta):
    def processAcars(self, acars: dict, icao: str = None):
        if "flight" in acars:
            flight_id = acars["flight"]
        elif "reg" in acars:
            flight_id = acars['reg'].lstrip(".")
        else:
            return

        if "arinc622" in acars:
            arinc622 = acars["arinc622"]
            if "adsc" in arinc622:
                adsc = arinc622["adsc"]
                if "tags" in adsc:
                    for tag in adsc["tags"]:
                        if "basic_report" in tag:
                            basic_report = tag["basic_report"]
                            msg = {
                                "lat": basic_report["lat"],
                                "lon": basic_report["lon"],
                                "altitude": basic_report["alt"]
                            }
                            if icao is not None:
                                source = IcaoSource(icao, humanReadable=flight_id)
                            else:
                                source = AcarsSource(flight_id)
                            Map.getSharedInstance().updateLocation(
                                source, AirplaneLocation(msg), "ACARS over {}".format(self.mode)
                            )
