from owrx.source.connector import ConnectorSource, ConnectorDeviceDescription
from owrx.command import Flag, Option
from typing import List
from owrx.form.input import Input, TextInput
from owrx.form.input.device import BiasTeeInput, DirectSamplingInput
from owrx.form.input.validator import Range


class RtlSdrSource(ConnectorSource):
    def getCommandMapper(self):
        return (
            super()
            .getCommandMapper()
            .setBase("rtl_connector")
            .setMappings({"bias_tee": Flag("-b"), "direct_sampling": Option("-e")})
        )


class RtlSdrDeviceDescription(ConnectorDeviceDescription):
    def getName(self):
        return "RTL-SDR device"

    def getInputs(self) -> List[Input]:
        return super().getInputs() + [
            TextInput(
                "device",
                "Device identifier",
                infotext="Device serial number or index",
            ),
            BiasTeeInput(),
            DirectSamplingInput(),
        ]

    def getDeviceOptionalKeys(self):
        return super().getDeviceOptionalKeys() + ["device", "bias_tee", "direct_sampling"]

    def getProfileOptionalKeys(self):
        return super().getProfileOptionalKeys() + ["bias_tee", "direct_sampling"]

    def getSampleRateRanges(self) -> List[Range]:
        return [Range(250000, 3200000)]
