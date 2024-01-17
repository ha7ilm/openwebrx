from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form.input.validator import Range


class RadioberrySource(SoapyConnectorSource):
    def getDriver(self):
        return "radioberry"


class RadioberryDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "RadioBerry"

    def getSampleRateRanges(self) -> list[Range]:
        return [
            Range(48000),
            Range(96000),
            Range(192000),
            Range(384000),
        ]
