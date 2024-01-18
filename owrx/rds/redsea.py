from pycsdr.modules import ExecModule
from pycsdr.types import Format


class RedseaModule(ExecModule):
    def __init__(self, sampleRate: int):
        super().__init__(
            Format.SHORT,
            Format.CHAR,
            ["redsea", "--input", "mpx", "--samplerate", str(sampleRate)]
        )
