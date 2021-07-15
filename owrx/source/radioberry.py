from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription


class RadioberrySource(SoapyConnectorSource):
    def getDriver(self):
        return "radioberry"


class RadioberryDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "RadioBerry"
