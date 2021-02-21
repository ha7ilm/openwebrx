from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form import Input
from owrx.form.device import BiasTeeInput
from typing import List


class HackrfSource(SoapyConnectorSource):
    def getSoapySettingsMappings(self):
        mappings = super().getSoapySettingsMappings()
        mappings.update({"bias_tee": "bias_tx"})
        return mappings

    def getDriver(self):
        return "hackrf"


class HackrfDeviceDescription(SoapyConnectorDeviceDescription):
    def getInputs(self) -> List[Input]:
        return super().getInputs() + [BiasTeeInput()]

    def getOptionalKeys(self):
        return super().getOptionalKeys() + ["bias_tee"]

    # TODO: find actual gain stages for hackrf
    # def getGainStages(self):
    #    return None
