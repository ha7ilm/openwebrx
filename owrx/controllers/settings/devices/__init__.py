from owrx.form import Input
from owrx.controllers.settings import Section
from abc import ABC, abstractmethod
from typing import List


class SdrDeviceType(ABC):
    @staticmethod
    def getByType(sdr_type: str) -> "SdrDeviceType":
        try:
            className = "".join(x for x in sdr_type.title() if x.isalnum()) + "DeviceType"
            module = __import__("owrx.controllers.settings.devices.{0}".format(sdr_type), fromlist=[className])
            cls = getattr(module, className)
            return cls()
        except ModuleNotFoundError:
            return None

    @abstractmethod
    def getInputs(self) -> List[Input]:
        pass

    def getSection(self):
        return Section("Device settings", *self.getInputs())
