from owrx.form import Input
from owrx.controllers.settings import Section
from abc import ABC, abstractmethod
from typing import List


class SdrDeviceDescriptionMissing(Exception):
    pass


class SdrDeviceDescription(ABC):
    @staticmethod
    def getByType(sdr_type: str) -> "SdrDeviceDescription":
        try:
            className = "".join(x for x in sdr_type.title() if x.isalnum()) + "DeviceDescription"
            module = __import__("owrx.source.{0}".format(sdr_type), fromlist=[className])
            cls = getattr(module, className)
            return cls()
        except (ModuleNotFoundError, AttributeError):
            raise SdrDeviceDescriptionMissing("Device description for type {} not available".format(sdr_type))

    @abstractmethod
    def getInputs(self) -> List[Input]:
        pass

    def getSection(self):
        return Section("Device settings", *self.getInputs())
