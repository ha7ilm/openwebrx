from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form.input.validator import Range
from typing import List


class RadioberrySource(SoapyConnectorSource):
    def getDriver(self):
        return "radioberry"


class RadioberryDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "RadioBerry"

    def getSampleRateRanges(self) -> List[Range]:
        return [
            Range(48000),
            Range(96000),
            Range(192000),
            Range(384000),
        ]
