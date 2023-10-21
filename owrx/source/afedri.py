from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form.input import Input, CheckboxInput, NumberInput
from owrx.form.input.device import RemoteInput
from owrx.form.input.validator import RangeValidator
from typing import List


AFEDRI_DEVICE_KEYS = ["rx_mode", "force_set_channel"]
AFEDRI_PROFILE_KEYS = ["r820t_lna_agc", "r820t_mixer_agc"]


class AfedriSource(SoapyConnectorSource):
    def getSoapySettingsMappings(self):
        mappings = super().getSoapySettingsMappings()
        mappings.update({x: x for x in AFEDRI_PROFILE_KEYS})
        return mappings

    def getEventNames(self):
        return super().getEventNames() + ["remote"] + AFEDRI_DEVICE_KEYS

    def getDriver(self):
        return "afedri"

    def buildSoapyDeviceParameters(self, parsed, values):
        params = super().buildSoapyDeviceParameters(parsed, values)
        params = [v for v in params if not "remote" in params]
        remote = values["remote"]
        address, port = remote.split(":")
        params += [{"address": address, "port": port}]

        can_be_set_at_start = AFEDRI_DEVICE_KEYS
        for elm in can_be_set_at_start:
            if elm in values:
                params += [{elm: values[elm]}]

        return params


class AfedriDeviceDescription(SoapyConnectorDeviceDescription):
    def getName(self):
        return "Afedri device"

    def supportsPpm(self):
        # not currently mapped, and it's unclear how this should be sent to the device
        return False

    def hasAgc(self):
        # not currently mapped
        return False

    def getInputs(self) -> List[Input]:
        return super().getInputs() + [
            RemoteInput(),
            CheckboxInput(
                "r820t_lna_agc",
                "Enable R820T LNA AGC",
            ),
            CheckboxInput(
                "r820t_mixer_agc",
                "Enable R820T Mixer AGC",
            ),
            NumberInput(
                "force_set_channel",
                "Use this channel instead of default when connect to master seed server.",
                "Number in range [0,3]",
                validator=RangeValidator(0, 3),
            ),
            NumberInput(
                "rx_mode",
                "RX Mode (Single/Dual/Quad Channel)",
                "Number in range [0,5]. Switch device to specific RX mode. (Single/DualDiversity/Dual/DiversityInternal/QuadDiversity/Quad)",
                validator=RangeValidator(0, 5),
            ),
        ]

    def getDeviceMandatoryKeys(self):
        return super().getDeviceMandatoryKeys() + ["remote"]

    def getDeviceOptionalKeys(self):
        return super().getDeviceOptionalKeys() + AFEDRI_DEVICE_KEYS

    def getProfileOptionalKeys(self):
        return super().getProfileOptionalKeys() + AFEDRI_PROFILE_KEYS

    def getGainStages(self):
        return [
            "RF",
            "FE",
            "R820T_LNA_GAIN",
            "R820T_MIXER_GAIN",
            "R820T_VGA_GAIN",
        ]
