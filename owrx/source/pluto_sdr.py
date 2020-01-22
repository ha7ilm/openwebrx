from .soapy import SoapyConnectorSource


class PlutoSdrSource(SoapyConnectorSource):
    def getDriver(self):
        return "plutosdr"
