from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form.input.validator import Range


class BladerfSource(SoapyConnectorSource):
    def getDriver(self):
        return "bladerf"


class BladerfDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "Blade RF"

    def getSampleRateRanges(self) -> list[Range]:
        return [Range(160000, 40000000)]
