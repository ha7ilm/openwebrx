from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription


class FcdppSource(SoapyConnectorSource):
    def getDriver(self):
        return "fcdpp"


class FcdppDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "FunCube Dongle Pro+"
