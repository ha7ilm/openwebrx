from typing import List
from owrx.controllers.settings.devices import SdrDeviceType
from owrx.form import Input, TextInput


class RtlSdrDeviceType(SdrDeviceType):
    def getInputs(self) -> List[Input]:
        return [
            TextInput(
                "test",
                "This is a drill"
            ),
        ]
