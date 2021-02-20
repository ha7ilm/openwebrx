from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription


class RedPitayaSource(SoapyConnectorSource):
    def getDriver(self):
        return "redpitaya"


class RedPitayaDeviceDescription(SoapyConnectorDeviceDescription):
    pass
