from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form.input.validator import Range


class PlutoSdrSource(SoapyConnectorSource):
    def getDriver(self):
        return "plutosdr"


class PlutoSdrDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "PlutoSDR"

    def getSampleRateRanges(self) -> list[Range]:
        return [Range(520833, 61440000)]
