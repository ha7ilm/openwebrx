from .soapy import SoapyConnectorSource


class PlutoSdrSource(SoapyConnectorSource):
    def getDriver(self):
        return "pluto_sdr"
