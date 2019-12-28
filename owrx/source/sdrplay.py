from .soapy import SoapyConnectorSource


class SdrplaySource(SoapyConnectorSource):
    def getDriver(self):
        return "sdrplay"
