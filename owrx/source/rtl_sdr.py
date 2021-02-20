from owrx.source.connector import ConnectorSource, ConnectorDeviceDescription
from owrx.command import Flag, Option
from typing import List
from owrx.form import Input, TextInput
from owrx.form.converter import OptionalConverter
from owrx.form.device import BiasTeeInput, DirectSamplingInput


class RtlSdrSource(ConnectorSource):
    def getCommandMapper(self):
        return (
            super()
            .getCommandMapper()
            .setBase("rtl_connector")
            .setMappings({"bias_tee": Flag("-b"), "direct_sampling": Option("-e")})
        )


class RtlSdrDeviceDescription(ConnectorDeviceDescription):
    def getInputs(self) -> List[Input]:
        return self.mergeInputs(
            super().getInputs(),
            [
                TextInput(
                    "device",
                    "Device identifier",
                    infotext="Device serial number or index",
                    converter=OptionalConverter(),
                ),
                BiasTeeInput(),
                DirectSamplingInput()
            ],
        )
