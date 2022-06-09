from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form.input import Input, CheckboxInput
from owrx.form.input.device import BiasTeeInput
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
    def getName(self):
        return "Airspy R2 or Mini"

    def supportsPpm(self):
        # not supported by the device API
        # frequency calibration can be done with separate tools and will be persisted on the device.
        # see discussion here: https://groups.io/g/openwebrx/topic/79360293
        return False

    def getInputs(self) -> List[Input]:
        return super().getInputs() + [
            BiasTeeInput(),
            CheckboxInput(
                "bitpack",
                "Enable bit-packing",
                infotext="Packs two 12-bit samples into 3 bytes."
                + " Lowers USB bandwidth consumption, increases CPU load",
            ),
        ]

    def getDeviceOptionalKeys(self):
        return super().getDeviceOptionalKeys() + ["bias_tee", "bitpack"]

    def getProfileOptionalKeys(self):
        return super().getProfileOptionalKeys() + ["bias_tee"]

    def getGainStages(self):
        return ["LNA", "MIX", "VGA"]
