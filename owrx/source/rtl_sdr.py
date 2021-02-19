from .connector import ConnectorSource
from owrx.command import Flag, Option
from owrx.controllers.settings.device import SdrDeviceDescription
from typing import List
from owrx.form import Input, TextInput


class RtlSdrSource(ConnectorSource):
    def getCommandMapper(self):
        return (
            super()
            .getCommandMapper()
            .setBase("rtl_connector")
            .setMappings({"bias_tee": Flag("-b"), "direct_sampling": Option("-e")})
        )


class RtlSdrDeviceDescription(SdrDeviceDescription):
    def getInputs(self) -> List[Input]:
        return self.mergeInputs(
            super().getInputs(),
            [
                TextInput("test", "This is a drill"),
            ],
        )
