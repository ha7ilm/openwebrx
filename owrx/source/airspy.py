from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form import Input, CheckboxInput
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
        return super().getInputs() + [
            BiasTeeInput(),
            CheckboxInput(
                "bitpack",
                "Enable bit-packing",
                infotext="Packs two 12-bit samples into 3 bytes."
                + " Lowers USB bandwidth consumption, increases CPU load",
            ),
        ]

    def getOptionalKeys(self):
        return super().getOptionalKeys() + ["bias_tee", "bitpack"]

    # TODO: find actual gain stages for airspay
    # def getGainStages(self):
    #    return None
