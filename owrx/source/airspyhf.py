from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form.input.validator import Range
from typing import List


class AirspyhfSource(SoapyConnectorSource):
    def getDriver(self):
        return "airspyhf"


class AirspyhfDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "Airspy HF+ or Discovery"

    def supportsPpm(self):
        # not currently supported by the SoapySDR module.
        return False

    def getSampleRateRanges(self) -> List[Range]:
        return [
            Range(192000),
            Range(256000),
            Range(384000),
            Range(456000),
            Range(768000),
            Range(912000),
        ]
