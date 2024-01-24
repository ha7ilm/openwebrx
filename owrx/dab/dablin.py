from pycsdr.modules import ExecModule
from pycsdr.types import Format


class DablinModule(ExecModule):
    def __init__(self):
        self.serviceId = 0
        super().__init__(
            Format.CHAR,
            Format.FLOAT,
            self._buildArgs()
        )

    def _buildArgs(self):
        return ["dablin", "-p", "-s", "{:#06x}".format(self.serviceId)]

    def setDabServiceId(self, serviceId: int) -> None:
        self.serviceId = serviceId
        self.setArgs(self._buildArgs())
        self.restart()
