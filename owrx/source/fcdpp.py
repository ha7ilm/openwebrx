from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form.input.validator import Range


class FcdppSource(SoapyConnectorSource):
    def getDriver(self):
        return "fcdpp"


class FcdppDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "FunCube Dongle Pro+"

    def getSampleRateRanges(self) -> list[Range]:
        return [
            Range(96000),
            Range(192000),
        ]
