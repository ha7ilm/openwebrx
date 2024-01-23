from pycsdr.modules import ExecModule
from pycsdr.types import Format


class DablinModule(ExecModule):
    def __init__(self):
        super().__init__(
            Format.CHAR,
            Format.FLOAT,
            ["dablin", "-1", "-p"]
        )
