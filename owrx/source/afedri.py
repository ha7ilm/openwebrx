import re
from ipaddress import IPv4Address, AddressValueError
from owrx.source.soapy import SoapyConnectorSource, SoapyConnectorDeviceDescription
from owrx.form.input import Input, CheckboxInput, DropdownInput, Option
from owrx.form.input.device import TextInput
from owrx.form.input.validator import Validator, ValidationError
from typing import List


AFEDRI_DEVICE_KEYS = ["rx_mode"]
AFEDRI_PROFILE_KEYS = ["r820t_lna_agc", "r820t_mixer_agc"]


class IPv4AndPortValidator(Validator):
    def validate(self, key, value) -> None:
        parts = value.split(":")
        if len(parts) != 2:
            raise ValidationError(key, "Wrong format. Expected IPv4:port")

        try:
            IPv4Address(parts[0])
        except AddressValueError as e:
            raise ValidationError(key, "IP address error: {}".format(str(e)))

        try:
            port = int(parts[1])
        except ValueError:
            raise ValidationError(key, "Port number invalid")
        if not 0 <= port <= 65535:
            raise ValidationError(key, "Port number out of range")


class AfedriAddressPortInput(TextInput):
    def __init__(self):
        super().__init__(
            "afedri_adress_port",
            "Afedri IP and Port",
            infotext="Afedri IP and port to connect to. Format = IPv4:Port",
            validator=IPv4AndPortValidator(),
        )


class AfedriSource(SoapyConnectorSource):
    def getSoapySettingsMappings(self):
        mappings = super().getSoapySettingsMappings()
        mappings.update({x: x for x in AFEDRI_PROFILE_KEYS})
        return mappings

    def getEventNames(self):
        return super().getEventNames() + ["afedri_adress_port"] + AFEDRI_DEVICE_KEYS

    def getDriver(self):
        return "afedri"

    def buildSoapyDeviceParameters(self, parsed, values):
        params = super().buildSoapyDeviceParameters(parsed, values)

        address, port = values["afedri_adress_port"].split(":")
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
            AfedriAddressPortInput(),
            CheckboxInput(
                "r820t_lna_agc",
                "Enable R820T LNA AGC",
            ),
            CheckboxInput(
                "r820t_mixer_agc",
                "Enable R820T Mixer AGC",
            ),
            DropdownInput(
                "rx_mode",
                "Switch the device to a specific RX mode at start",
                options=[
                    Option("0", "Single"),
                    Option("1", "DualDiversity"),
                    Option("2", "Dual"),
                    Option("3", "DiversityInternal"),
                    Option("4", "QuadDiversity"),
                    Option("5", "Quad"),
                ],
            ),
        ]

    def getDeviceMandatoryKeys(self):
        return super().getDeviceMandatoryKeys() + ["afedri_adress_port"]

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

    def getNumberOfChannels(self) -> int:
        return 4
