from pycsdr.modules import ExecModule
from pycsdr.types import Format


class DrmModule(ExecModule):
    def __init__(self):
        super().__init__(
            Format.COMPLEX_SHORT,
            Format.SHORT,
            ["dream", "-c", "6", "--sigsrate", "48000", "--audsrate", "48000", "-I", "-", "-O", "-"]
        )
