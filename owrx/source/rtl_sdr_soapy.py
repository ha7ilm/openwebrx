from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form import Input
from owrx.form.device import BiasTeeInput, DirectSamplingInput
from typing import List


class RtlSdrSoapySource(SoapyConnectorSource):
    def getSoapySettingsMappings(self):
        mappings = super().getSoapySettingsMappings()
        mappings.update({"direct_sampling": "direct_samp", "bias_tee": "biastee"})
        return mappings

    def getDriver(self):
        return "rtlsdr"


class RtlSdrSoapyDeviceDescription(SoapyConnectorDeviceDescription):
    def getInputs(self) -> List[Input]:
        return super().getInputs() + [BiasTeeInput(), DirectSamplingInput()]

    def getOptionalKeys(self):
        return super().getOptionalKeys() + ["bias_tee", "direct_sampling"]

    def getProfileOptionalKeys(self):
        return super().getProfileOptionalKeys() + ["bias_tee", "direct_sampling"]
