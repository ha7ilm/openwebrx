from owrx.source.connector import ConnectorSource, ConnectorDeviceDescription
from owrx.form.input.validator import Range
from typing import List


class SddcSource(ConnectorSource):
    def getCommandMapper(self):
        return super().getCommandMapper().setBase("sddc_connector")


class SddcDeviceDescription(ConnectorDeviceDescription):
    def getName(self):
        return "BBRF103 / RX666 / RX888 device (libsddc)"

    def hasAgc(self):
        return False

    def getSampleRateRanges(self) -> List[Range]:
        # resampling is done in software... it can't cover the full range, but it's not finished either.
        return [Range(0, 64000000)]
