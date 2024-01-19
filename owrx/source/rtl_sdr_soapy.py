from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form.input import Input
from owrx.form.input.device import BiasTeeInput, DirectSamplingInput
from owrx.form.input.validator import Range
from typing import List


class RtlSdrSoapySource(SoapyConnectorSource):
    def getSoapySettingsMappings(self):
        mappings = super().getSoapySettingsMappings()
        mappings.update({"direct_sampling": "direct_samp", "bias_tee": "biastee"})
        return mappings

    def getDriver(self):
        return "rtlsdr"


class RtlSdrSoapyDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "RTL-SDR device (via SoapySDR)"

    def getInputs(self) -> List[Input]:
        return super().getInputs() + [BiasTeeInput(), DirectSamplingInput()]

    def getDeviceOptionalKeys(self):
        return super().getDeviceOptionalKeys() + ["bias_tee", "direct_sampling"]

    def getProfileOptionalKeys(self):
        return super().getProfileOptionalKeys() + ["bias_tee", "direct_sampling"]

    def getSampleRateRanges(self) -> List[Range]:
        return [Range(250000, 3200000)]
