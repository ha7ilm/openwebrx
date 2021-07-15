from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription


class LimeSdrSource(SoapyConnectorSource):
    def getDriver(self):
        return "lime"


class LimeSdrDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "LimeSDR device"
