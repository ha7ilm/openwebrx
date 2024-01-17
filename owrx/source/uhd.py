from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form.input.validator import Range


class UhdSource(SoapyConnectorSource):
    def getDriver(self):
        return "uhd"


class UhdDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "Ettus Research USRP device"

    def getSampleRateRanges(self) -> list[Range]:
        # not sure since this depends of the specific model
        return [Range(0, 64000000)]
