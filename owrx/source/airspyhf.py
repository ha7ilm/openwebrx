from .airspy import AirspySource


class AirspyhfSource(AirspySource):
    def getDriver(self):
        return "airspyhf"
