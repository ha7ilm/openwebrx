from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form import Input
from owrx.form.device import BiasTeeInput
from typing import List


class AirspySource(SoapyConnectorSource):
    def getSoapySettingsMappings(self):
        mappings = super().getSoapySettingsMappings()
        mappings.update(
            {
                "bias_tee": "biastee",
                "bitpack": "bitpack",
            }
        )
        return mappings

    def getDriver(self):
        return "airspy"


class AirspyDeviceDescription(SoapyConnectorDeviceDescription):
    def getInputs(self) -> List[Input]:
        return self.mergeInputs(super().getInputs(), [BiasTeeInput()])
