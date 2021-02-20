from owrx.source.connector import ConnectorSource, ConnectorDeviceDescription
from owrx.command import Flag, Option, Argument
from owrx.form import Input
from owrx.form.device import RemoteInput
from typing import List


class RtlTcpSource(ConnectorSource):
    def getCommandMapper(self):
        return (
            super()
            .getCommandMapper()
            .setBase("rtl_tcp_connector")
            .setMappings(
                {
                    "bias_tee": Flag("-b"),
                    "direct_sampling": Option("-e"),
                    "remote": Argument(),
                }
            )
        )


class RtlTcpDeviceDescription(ConnectorDeviceDescription):
    def getInputs(self) -> List[Input]:
        return self.mergeInputs(super().getInputs(), [RemoteInput()])
