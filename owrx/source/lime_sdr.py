from .soapy import SoapyConnectorSource


class LimeSdrSource(SoapyConnectorSource):
    def getDriver(self):
        return "lime"
