from owrx.source.connector import ConnectorSource, ConnectorDeviceDescription
from owrx.command import Argument, Flag, Option
from owrx.form import Input, DropdownInput, DropdownEnum, CheckboxInput
from owrx.form.device import RemoteInput
from owrx.form.converter import OptionalConverter
from typing import List


class RundsSource(ConnectorSource):
    def getCommandMapper(self):
        return (
            super()
            .getCommandMapper()
            .setBase("runds_connector")
            .setMappings(
                {
                    "long": Flag("-l"),
                    "remote": Argument(),
                    "protocol": Option("-m"),
                }
            )
        )


class ProtocolOptions(DropdownEnum):
    PROTOCOL_EB200 = ("eb200", "EB200 protocol")
    PROTOCOL_AMMOS = ("ammos", "Ammos protocol")

    def __new__(cls, *args, **kwargs):
        value, description = args
        obj = object.__new__(cls)
        obj._value_ = value
        obj.description = description
        return obj

    def __str__(self):
        return self.description


class RundsDeviceDescription(ConnectorDeviceDescription):
    def getInputs(self) -> List[Input]:
        return self.mergeInputs(
            super().getInputs(),
            [
                RemoteInput(),
                DropdownInput("protocol", "Protocol", ProtocolOptions),
                CheckboxInput(
                    "long", "", "Use 32-bit sample size (LONG)", converter=OptionalConverter(defaultFormValue=False)
                ),
            ],
        )
