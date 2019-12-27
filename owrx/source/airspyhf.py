from .soapy import SoapyConnectorSource


class AirspyhfSource(SoapyConnectorSource):
    def getDriver(self):
        return "airspyhf"
