from owrx.form import Input
from owrx.controllers.settings import Section
from typing import List


class SdrDeviceDescriptionMissing(Exception):
    pass


class SdrDeviceDescription(object):
    @staticmethod
    def getByType(sdr_type: str) -> "SdrDeviceDescription":
        try:
            className = "".join(x for x in sdr_type.title() if x.isalnum()) + "DeviceDescription"
            module = __import__("owrx.source.{0}".format(sdr_type), fromlist=[className])
            cls = getattr(module, className)
            return cls()
        except (ModuleNotFoundError, AttributeError):
            raise SdrDeviceDescriptionMissing("Device description for type {} not available".format(sdr_type))

    def getInputs(self) -> List[Input]:
        return []

    def mergeInputs(self, *args):
        # build a dictionary indexed by the input id to make sure every id only exists once
        inputs = {input.id: input for input_list in args for input in input_list}
        return inputs.values()

    def getSection(self):
        return Section("Device settings", *self.getInputs())
