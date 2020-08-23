from owrx.source.soapy import SoapyConnectorSource


class FcdppSource(SoapyConnectorSource):
    def getDriver(self):
        return "fcdpp"
