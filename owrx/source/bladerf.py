from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription


class BladerfSource(SoapyConnectorSource):
    def getDriver(self):
        return "bladerf"


class BladerfDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "Blade RF"
