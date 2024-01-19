from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form.input.validator import Range
from typing import List


class LimeSdrSource(SoapyConnectorSource):
    def getDriver(self):
        return "lime"


class LimeSdrDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "LimeSDR device"

    def getSampleRateRanges(self) -> List[Range]:
        return [Range(100000, 65000000)]
