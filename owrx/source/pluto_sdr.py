from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form.input.validator import Range
from typing import List


class PlutoSdrSource(SoapyConnectorSource):
    def getDriver(self):
        return "plutosdr"


class PlutoSdrDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "PlutoSDR"

    def getSampleRateRanges(self) -> List[Range]:
        return [Range(520833, 61440000)]
