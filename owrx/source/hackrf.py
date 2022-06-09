from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form.input import Input
from owrx.form.input.device import BiasTeeInput
from typing import List


class HackrfSource(SoapyConnectorSource):
    def getSoapySettingsMappings(self):
        mappings = super().getSoapySettingsMappings()
        mappings.update({"bias_tee": "bias_tx"})
        return mappings

    def getDriver(self):
        return "hackrf"


class HackrfDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "HackRF"

    def supportsPpm(self):
        # not implemented by the SoapySDR module.
        # see discussion here: https://groups.io/g/openwebrx/topic/78339109
        return False

    def getInputs(self) -> List[Input]:
        return super().getInputs() + [BiasTeeInput()]

    def getDeviceOptionalKeys(self):
        return super().getDeviceOptionalKeys() + ["bias_tee"]

    def getProfileOptionalKeys(self):
        return super().getProfileOptionalKeys() + ["bias_tee"]

    def getGainStages(self):
        return ["LNA", "AMP", "VGA"]
