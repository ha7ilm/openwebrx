from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form.input import Input, TextInput
from owrx.form.input.validator import Range
from typing import List


class PlutoSdrSource(SoapyConnectorSource):
    def getDriver(self):
        return "plutosdr"

    def getEventNames(self):
        return super().getEventNames() + ["hostname"]

    def buildSoapyDeviceParameters(self, parsed, values):
        params = super().buildSoapyDeviceParameters(parsed, values)
        if "hostname" in values:
            params = [p for p in params if "hostname" not in p]
            params += [{"hostname": values["hostname"]}]
        return params


class PlutoSdrDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "PlutoSDR"

    def getInputs(self) -> List[Input]:
        return super().getInputs() + [
            TextInput(
                "hostname",
                "Hostname",
                infotext="Use this for PlutoSDR devices attached to the network"
            )
        ]

    def getDeviceOptionalKeys(self):
        return super().getDeviceOptionalKeys() + ["hostname"]

    def getSampleRateRanges(self) -> List[Range]:
        return [Range(520833, 61440000)]
