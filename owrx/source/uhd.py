from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription


class UhdSource(SoapyConnectorSource):
    def getDriver(self):
        return "uhd"


class UhdDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "Ettus Research USRP device"
