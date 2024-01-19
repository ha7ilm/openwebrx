from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form.input.validator import Range
from typing import List


class FcdppSource(SoapyConnectorSource):
    def getDriver(self):
        return "fcdpp"


class FcdppDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "FunCube Dongle Pro+"

    def getSampleRateRanges(self) -> List[Range]:
        return [
            Range(96000),
            Range(192000),
        ]
